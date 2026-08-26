"""Route SRBench's LLM calls through hyra's local Anthropic-compatible proxy.

hyra (``/data/workspace/data1/hyra``) already integrates several upstream models
behind an OpenAI/Bedrock/Responses gateway.  Its ``hyra.claude_api_compat`` module
starts a small loopback HTTP server that *speaks native Anthropic Messages* and
translates each request to whatever transport the chosen model needs.  Because
SRBench's model layer already builds an ``anthropic.Anthropic`` client with a
configurable ``base_url``, we can reuse hyra's proxy verbatim: point the client at
the loopback URL and let the proxy do the transport translation.

This module owns the preset table (which upstream model + transport for each
short name), recovers the gateway credential, and starts/caches one long-lived
proxy per preset for the lifetime of the process.

Two presets are exposed, matching hyra's ``run_gongfeng.sh`` MODEL_PRESET:
  * ``opus-4.8``    — Claude Opus 4.8 via AWS Bedrock invoke (api_format=bedrock)
  * ``gpt-5.6-sol`` — GPT-5.6-Sol via Azure Responses API (api_format=openai-responses,
                      the only route running tools+reasoning together, effort=max)
"""

from __future__ import annotations

import atexit
import hashlib
import os
import sys
import threading
from pathlib import Path
from typing import Any

# Where the hyra project lives; override with SRBENCH_HYRA_ROOT if it moves.
HYRA_ROOT = os.environ.get("SRBENCH_HYRA_ROOT", "/data/workspace/data1/hyra")

# Preset table. ``key_query`` is appended to the raw gateway credential
# (APPID:APPKEY) to form the upstream api_key; ``{cache_id}`` is filled in per
# process.  These mirror hyra/run_gongfeng.sh exactly (verified live).
PRESETS: dict[str, dict[str, Any]] = {
    "opus-4.8": {
        "base_url": "http://trpc-gpt-eval.production.polaris:8080",
        "api_format": "bedrock",
        "model": "anthropic.claude-opus-4-8",
        "reasoning_effort": None,
        "key_query": (
            "?provider=aws_third&model=anthropic.claude-opus-4-8"
            "&timeout=1200&cache_task_id={cache_id}"
        ),
    },
    "gpt-5.6-sol": {
        "base_url": "http://llm-api.model-eval.woa.com/v1",
        "api_format": "openai-responses",
        "model": "api_azure_openai_gpt-5.6-sol",
        "reasoning_effort": "max",
        "key_query": "?timeout=1200&cache_task_id={cache_id}",
    },
}

# The Anthropic SDK requires *some* api_key; the proxy authenticates upstream with
# the gateway credential and only uses the client key for session correlation, so
# any non-empty sentinel works.  hyra's own sentinel is imported below.

# Client-side read timeout.  gpt-5.6-sol at effort=max can take minutes per turn.
CLIENT_TIMEOUT = float(os.environ.get("SRBENCH_HYRA_CLIENT_TIMEOUT", "1200"))
PROXY_TIMEOUT = float(os.environ.get("SRBENCH_HYRA_PROXY_TIMEOUT", "1800"))
PROXY_MAX_TOKENS = int(os.environ.get("SRBENCH_HYRA_MAX_TOKENS", "32768"))

_LOCK = threading.Lock()
_PROXIES: dict[str, Any] = {}   # preset -> live proxy instance (base_url reachable)
_HOLDERS: list[Any] = []        # keep running_proxy wrappers alive for atexit
_CACHE_ID: str | None = None


def _ensure_hyra_on_path() -> None:
    root = str(Path(HYRA_ROOT).resolve())
    if root not in sys.path:
        sys.path.insert(0, root)
    if not (Path(root) / "hyra" / "claude_api_compat.py").exists():
        raise SystemExit(
            f"hyra not found at {root!r}. Set SRBENCH_HYRA_ROOT to the hyra project root "
            "(the directory containing the 'hyra/' package)."
        )


def _cache_task_id() -> str:
    """A stable-per-process id used for the gateway's cache_task_id knob."""
    global _CACHE_ID
    if _CACHE_ID is None:
        seed = f"{os.getpid()}-{HYRA_ROOT}-{os.environ.get('SRBENCH_HYRA_CACHE_SALT', '')}"
        _CACHE_ID = hashlib.md5(seed.encode()).hexdigest()
    return _CACHE_ID


def _gateway_cred() -> str:
    """Recover the raw gateway credential (APPID:APPKEY), no query suffix.

    Priority: HYRA_GATEWAY_CRED → HYRA_CLAUDE_API_KEY (strip any ``?...``) →
    parse ``<HYRA_ROOT>/.env``.
    """
    cred = os.environ.get("HYRA_GATEWAY_CRED")
    if cred:
        return cred.split("?", 1)[0].strip()

    full = os.environ.get("HYRA_CLAUDE_API_KEY")
    if full:
        return full.split("?", 1)[0].strip()

    env_path = Path(HYRA_ROOT) / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("HYRA_CLAUDE_API_KEY="):
                return line.split("=", 1)[1].split("?", 1)[0].strip()

    raise SystemExit(
        "Missing gateway credential. Set HYRA_GATEWAY_CRED (APPID:APPKEY), or "
        f"ensure HYRA_CLAUDE_API_KEY is set, or that {env_path} contains it."
    )


def available_presets() -> list[str]:
    return sorted(PRESETS)


def start_proxy(preset: str) -> tuple[str, str, str]:
    """Start (or reuse) hyra's loopback proxy for ``preset``.

    Returns ``(base_url, sentinel_api_key, upstream_model)``.  The proxy is
    started once per preset and kept alive for the whole process; an atexit hook
    stops every proxy on exit.
    """
    if preset not in PRESETS:
        raise SystemExit(
            f"Unknown hyra preset {preset!r}. Choose one of: {', '.join(available_presets())}."
        )

    with _LOCK:
        existing = _PROXIES.get(preset)
        if existing is not None:
            return existing.base_url, _sentinel_key(), PRESETS[preset]["model"]

        _ensure_hyra_on_path()
        from hyra.claude_api_compat import (  # noqa: E402  (path set above)
            build_run_eval_claude_config,
            running_proxy,
        )

        spec = PRESETS[preset]
        cred = _gateway_cred()
        api_key = cred + spec["key_query"].format(cache_id=_cache_task_id())
        cfg = build_run_eval_claude_config(
            api_key=api_key,
            base_url=spec["base_url"],
            model=spec["model"],
            api_format=spec["api_format"],
            reasoning_effort=spec["reasoning_effort"],
            timeout=PROXY_TIMEOUT,
            max_tokens=PROXY_MAX_TOKENS,
            dump_io=False,  # avoid multi-threaded file contention under --workers
        )
        holder = running_proxy(cfg)          # selects the right *ClaudeProxy class
        proxy = holder.proxy
        proxy.start()                        # binds an ephemeral loopback port
        _PROXIES[preset] = proxy
        _HOLDERS.append(holder)
        return proxy.base_url, _sentinel_key(), spec["model"]


def _sentinel_key() -> str:
    _ensure_hyra_on_path()
    from hyra.claude_api_compat import PROXY_API_KEY  # noqa: E402
    return PROXY_API_KEY


def make_anthropic_client(preset: str):
    """Convenience: start the proxy and return a ready ``anthropic.Anthropic``."""
    import anthropic

    base_url, key, _ = start_proxy(preset)
    return anthropic.Anthropic(base_url=base_url, api_key=key, timeout=CLIENT_TIMEOUT)


@atexit.register
def _shutdown_proxies() -> None:
    for holder in _HOLDERS:
        try:
            holder.proxy.stop()
        except Exception:
            pass


if __name__ == "__main__":  # tiny smoke: start a proxy and print its URL
    name = sys.argv[1] if len(sys.argv) > 1 else "opus-4.8"
    url, sentinel, model = start_proxy(name)
    print(f"preset={name} model={model} base_url={url} key={sentinel}")
