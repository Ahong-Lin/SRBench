#!/usr/bin/env python3
"""Long-lived hyra proxy for harbor runs: Anthropic-native on the wire, gateway upstream.

Harbor's docker backend runs each trial's ``claude`` CLI inside a container, so the
proxy must be reachable from that container -- not just from loopback. Bind
``0.0.0.0`` on a FIXED port and hand the container the docker bridge gateway IP
(172.17.0.1 by default), which is reachable from a default-bridge container with no
``--add-host`` needed (verified empirically).

The gateway credential (APPID:APPKEY) is never hardcoded: it is recovered exactly the
way SRBench's ``hyra_provider`` does (HYRA_GATEWAY_CRED -> HYRA_CLAUDE_API_KEY ->
``<hyra>/.env``).

Usage:
    python3 proxy_daemon.py [--preset opus-4.8] [--port 8788] [--host 0.0.0.0]

Writes ``<statefile>`` (default /tmp/srbench_harbor_proxy.json) with the URL the
container should use, then blocks until SIGINT/SIGTERM.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import threading
from pathlib import Path

HYRA_ROOT = os.environ.get("SRBENCH_HYRA_ROOT", "/data/workspace/data1/hyra")
SRBENCH_ROOT = Path(__file__).resolve().parents[1]

# Presets beyond hyra_provider.PRESETS. Same aws_third Bedrock passthrough shape as
# opus-4.8, so the existing BedrockAnthropicClaudeProxy drives it unchanged.
#
# claude-haiku-4-5 (iwiki.woa.com/p/4018838598): 200k context, **8k max output**, and
# **no extended thinking**. The 8k ceiling is load-bearing -- the opus default of 32768
# is above the model's real limit. Claude Code requests 64000 every turn, and
# _capped_max_tokens takes min(client, ceiling), so the ceiling is what ships.
EXTRA_PRESETS = {
    "haiku-4.5": {
        "base_url": "http://trpc-gpt-eval.production.polaris:8080",
        "api_format": "bedrock",
        "model": "anthropic.claude-haiku-4-5-20251001-v1:0",
        "reasoning_effort": None,          # no extended thinking on this model
        "max_tokens": 8192,
        "no_thinking": True,               # see _install_no_thinking_shim
        "key_query": (
            "?provider=aws_third&model=anthropic.claude-haiku-4-5-20251001-v1:0"
            "&timeout=1200&cache_task_id={cache_id}"
        ),
    },
}


def _install_no_thinking_shim(cac, cfg) -> None:
    """Strip `thinking` / `output_config.effort` for models without extended thinking.

    Claude Code unconditionally sends `thinking={"type":"enabled","budget_tokens":N}`
    (measured: max_tokens=32000, budget_tokens=31999). Haiku 4.5 has no extended
    thinking, and the gateway rejects the related fields outright:
      * thinking.type=adaptive   -> 400 "adaptive thinking is not supported on this model"
      * output_config.effort     -> 400 "output_config.effort: Extra inputs are not permitted"
    Worse, `thinking.enabled` alone is *accepted*, so the failure only surfaces once the
    proxy caps max_tokens to the model's 8k limit while budget_tokens stays at 31999:
      * 400 "`max_tokens` must be greater than `thinking.budget_tokens`"
    That is the exact error that killed the first haiku trial (UnknownApiError).

    hyra's BedrockAnthropicClaudeProxy has no rewrite for this (opus-4.8 wants those
    fields kept), so drop them here in the one place both routes funnel through:
    _build_upstream_body, which runs after the max_tokens cap.
    """
    proxy_cls = cac.BedrockAnthropicClaudeProxy
    original = proxy_cls._build_upstream_body

    def patched(self, body):
        out = original(self, body)
        out.pop("thinking", None)
        oc = out.get("output_config")
        if isinstance(oc, dict):
            kept = {k: v for k, v in oc.items() if k != "effort"}
            if kept:
                out["output_config"] = kept
            else:
                out.pop("output_config", None)
        return out

    proxy_cls._build_upstream_body = patched


def bridge_gateway_ip(default: str = "172.17.0.1") -> str:
    """The docker bridge gateway -- the address a bridged container calls the host on."""
    try:
        out = subprocess.run(
            ["docker", "network", "inspect", "bridge",
             "--format", "{{range .IPAM.Config}}{{.Gateway}}{{end}}"],
            capture_output=True, text=True, timeout=30,
        )
        ip = out.stdout.strip()
        return ip or default
    except Exception:
        return default


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preset", default="opus-4.8")
    ap.add_argument("--port", type=int, default=8788)
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--max-tokens", type=int, default=None,
                    help="output-token CEILING; defaults to the preset's own limit")
    ap.add_argument("--timeout", type=float, default=3600.0)
    ap.add_argument("--statefile", default="/tmp/srbench_harbor_proxy.json")
    args = ap.parse_args()

    sys.path.insert(0, str(SRBENCH_ROOT))
    sys.path.insert(0, HYRA_ROOT)
    import hyra_provider as hp
    from hyra.claude_api_compat import (
        PROXY_API_KEY,
        build_run_eval_claude_config,
        running_proxy,
    )

    presets = dict(hp.PRESETS)
    presets.update(EXTRA_PRESETS)
    if args.preset not in presets:
        sys.exit(f"unknown preset {args.preset!r}; choose from {sorted(presets)}")
    spec = presets[args.preset]

    cred = hp._gateway_cred()                       # APPID:APPKEY, never logged
    api_key = cred + spec["key_query"].format(cache_id=hp._cache_task_id())

    cfg = build_run_eval_claude_config(
        api_key=api_key,
        base_url=spec["base_url"],
        model=spec["model"],
        api_format=spec["api_format"],
        reasoning_effort=spec["reasoning_effort"],
        timeout=args.timeout,
        # A ceiling, not an override (_capped_max_tokens). Must not exceed the
        # model's real output limit or the gateway 400s the request.
        max_tokens=args.max_tokens or spec.get("max_tokens", 32768),
        dump_io=False,                              # many concurrent trials, one file
    )
    cfg.host = args.host
    cfg.port = args.port

    # ThreadingHTTPServer's listen() backlog defaults to 5; N concurrent agents each
    # burst several requests per turn, so a short queue can refuse connections that
    # harbor would then classify as a network error. Cheap insurance.
    import hyra.claude_api_compat as _cac
    _cac._CompatHTTPServer.request_queue_size = 128

    if spec.get("no_thinking"):
        _install_no_thinking_shim(_cac, cfg)

    holder = running_proxy(cfg)
    proxy = holder.proxy
    proxy.start()

    # proxy.base_url echoes the BIND address (0.0.0.0), which is not dialable. Publish
    # the two addresses that are: loopback for host-side checks, bridge IP for containers.
    host_url = f"http://127.0.0.1:{args.port}"
    container_url = f"http://{bridge_gateway_ip()}:{args.port}"
    state = {
        "preset": args.preset,
        "model": spec["model"],
        "bind": f"{args.host}:{args.port}",
        "host_url": host_url,
        "container_url": container_url,
        "sentinel_api_key": PROXY_API_KEY,
        "appid": cred.split(":", 1)[0],             # id only; key never written
        "pid": os.getpid(),
    }
    Path(args.statefile).write_text(json.dumps(state, indent=2))

    print(json.dumps(state, indent=2), flush=True)
    print(f"[proxy] serving {spec['model']} -- ctrl-c to stop", flush=True)

    stop = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop.set())
    try:
        stop.wait()
    finally:
        proxy.stop()
        print("[proxy] stopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
