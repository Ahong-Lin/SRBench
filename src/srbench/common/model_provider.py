"""Shared Anthropic Messages and OpenAI-compatible Chat Completions adapter."""

from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from urllib.parse import urlsplit
from typing import Any, Literal

import anthropic
import httpx


Provider = Literal["anthropic", "openrouter", "openai"]


class ModelRequestError(RuntimeError):
    """A compact, provider-neutral error for a failed model request."""


class ModelServiceError(ModelRequestError):
    """Transport owns retries; generation must not retry this as bad model text."""

    def __init__(self, message: str, *, retryable: bool):
        super().__init__(message)
        self.retryable = retryable


def _chat_endpoint(base_url: str) -> str:
    """Accept either an API root or a fully-qualified chat endpoint."""
    endpoint = base_url.strip().rstrip("/")
    return endpoint if endpoint.endswith("/chat/completions") else endpoint + "/chat/completions"


def _anthropic_kwargs(
    api_key: str | None,
    auth_token: str | None,
    base_url: str | None,
    auth_source: str,
) -> dict[str, Any]:
    # An empty auth_token creates an invalid "Bearer " header in recent SDKs.
    # Omit the unselected header explicitly: older SDKs can inherit the other
    # credential from the environment even when the constructor receives None.
    api_key = (api_key or "").strip()
    auth_token = (auth_token or "").strip()
    kwargs: dict[str, Any] = {"api_key": None, "auth_token": None}
    if base_url:
        kwargs["base_url"] = base_url.strip()
    if auth_source == "api_key":
        if not api_key:
            raise SystemExit("Missing ANTHROPIC_API_KEY.")
        kwargs["api_key"] = api_key
        kwargs["default_headers"] = {"Authorization": anthropic.omit}
        return kwargs
    if auth_source == "auth_token":
        if not auth_token:
            raise SystemExit("Missing ANTHROPIC_AUTH_TOKEN.")
        kwargs["auth_token"] = auth_token
        kwargs["default_headers"] = {"X-Api-Key": anthropic.omit}
        return kwargs
    if api_key:
        kwargs["api_key"] = api_key
        kwargs["default_headers"] = {"Authorization": anthropic.omit}
        return kwargs
    if auth_token:
        kwargs["auth_token"] = auth_token
        kwargs["default_headers"] = {"X-Api-Key": anthropic.omit}
        return kwargs
    raise SystemExit("Missing ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN.")


def anthropic_runtime_env(base_url=None, auth_source="auto"):
    """Resolve the same endpoint and credential selection for the Claude SDK."""
    endpoint = base_url or os.environ.get("ANTHROPIC_BASE_URL") or "https://api.anthropic.com"
    kwargs = _anthropic_kwargs(os.environ.get("ANTHROPIC_API_KEY"),
                               os.environ.get("ANTHROPIC_AUTH_TOKEN"), endpoint, auth_source)
    return {"PATH": os.environ.get("PATH", ""), "ANTHROPIC_BASE_URL": kwargs["base_url"],
            "ANTHROPIC_API_KEY": kwargs["api_key"] or "",
            "ANTHROPIC_AUTH_TOKEN": kwargs["auth_token"] or ""}


class ModelCaller:
    """Make text or tool calls using the selected provider's credentials."""

    def __init__(
        self,
        provider: Provider,
        *,
        anthropic_client: anthropic.Anthropic | None = None,
        openrouter_api_key: str | None = None,
        openrouter_base_url: str | None = None,
        openai_api_key: str | None = None,
        openai_base_url: str | None = None,
    ) -> None:
        self.provider = provider
        self.anthropic_client = anthropic_client
        self.openrouter_api_key = openrouter_api_key
        self.openrouter_base_url = openrouter_base_url
        self.openai_api_key = openai_api_key
        self.openai_base_url = openai_base_url

    def complete(
        self,
        user_prompt: str,
        model: str,
        max_tokens: int,
        system_prompt: str | None = None,
        *,
        json_mode: bool = False,
    ) -> str:
        """Return the text portion of a one-shot completion."""
        if self.provider == "anthropic":
            if self.anthropic_client is None:  # pragma: no cover - setup guard
                raise ModelRequestError("Anthropic client was not initialized.")
            kwargs: dict[str, Any] = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": user_prompt}],
            }
            if system_prompt:
                kwargs["system"] = system_prompt
            try:
                message = self.anthropic_client.messages.create(**kwargs)
            except anthropic.APIError as exc:
                raise ModelRequestError(f"Anthropic request failed: {exc}") from exc
            text = "".join(
                getattr(block, "text", "")
                for block in message.content
                if getattr(block, "type", "") == "text"
            )
            if not text.strip():
                raise ModelRequestError("Anthropic returned an empty text response.")
            return text

        messages: list[dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        payload = self.chat(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            json_mode=json_mode,
        )
        content = payload["choices"][0]["message"].get("content")
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        if not isinstance(content, str) or not content.strip():
            raise ModelRequestError(
                f"{self.provider} returned an empty or non-text response: "
                + json.dumps(payload, ensure_ascii=False)[:1000]
            )
        return content

    def chat(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        max_tokens: int,
        tools: list[dict[str, Any]] | None = None,
        json_mode: bool = False,
    ) -> dict[str, Any]:
        """Call OpenAI or OpenRouter, preserving model IDs and tool messages."""
        if self.provider == "openai":
            api_key, base_url = self.openai_api_key, self.openai_base_url
            token_field = "max_completion_tokens"
        elif self.provider == "openrouter":
            api_key, base_url = self.openrouter_api_key, self.openrouter_base_url
            token_field = "max_tokens"
        else:
            raise ModelRequestError("Chat Completions requires the openai or openrouter provider.")
        if not api_key or not base_url:
            raise ModelRequestError(f"{self.provider} client was not initialized.")

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            token_field: max_tokens,
        }
        if json_mode and self.provider == "openai":
            payload["response_format"] = {"type": "json_object"}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        endpoint = _chat_endpoint(base_url)
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        if self.provider == "openrouter":
            headers.update({"HTTP-Referer": "https://github.com/llm-srbench",
                            "X-Title": "LLM-SRBench v7"})
        prefix = f"SRBENCH_{self.provider.upper()}"
        max_retries = int(os.environ.get(f"{prefix}_MAX_RETRIES", "1"))
        read_timeout = float(os.environ.get(f"{prefix}_READ_TIMEOUT", "300"))
        if max_retries < 0 or not math.isfinite(read_timeout) or read_timeout <= 0:
            raise ValueError("Model retries must be nonnegative and read timeout must be positive and finite")
        transient_statuses = {429, 500, 502, 503, 504}
        response: httpx.Response | None = None
        for attempt in range(max_retries + 1):
            started = time.monotonic()
            label = f"[model {self.provider}/{model} HTTP {attempt + 1}/{max_retries + 1}]"
            # Log timing and host only, never headers, credentials or request bodies.
            print(f"{label} start; host={urlsplit(endpoint).hostname}; read_timeout={read_timeout:g}s",
                  file=sys.stderr, flush=True)
            try:
                response = httpx.post(
                    endpoint,
                    headers=headers,
                    json=payload,
                    timeout=httpx.Timeout(read_timeout, connect=min(20.0, read_timeout)),
                )
            except httpx.HTTPError as exc:
                retryable = isinstance(exc, (httpx.TimeoutException, httpx.NetworkError,
                                             httpx.RemoteProtocolError, httpx.ProxyError))
                print(f"{label} {type(exc).__name__} after {time.monotonic() - started:.1f}s",
                      file=sys.stderr, flush=True)
                if not retryable or attempt >= max_retries:
                    raise ModelServiceError(f"{self.provider} connection failed: {type(exc).__name__}: {exc}",
                                            retryable=retryable) from exc
                time.sleep(min(30.0, 2 ** attempt) * random.random())
                continue
            print(f"{label} status={response.status_code}; elapsed={time.monotonic() - started:.1f}s",
                  file=sys.stderr, flush=True)
            if response.status_code not in transient_statuses or attempt >= max_retries:
                break
            time.sleep(min(30.0, 2 ** attempt) * random.random())
        if response is None:  # pragma: no cover - defensive setup guard
            raise ModelRequestError(f"{self.provider} request produced no response.")
        if response.is_error:
            try:
                error_payload = response.json()
                detail = error_payload.get("error", response.text) if isinstance(error_payload, dict) else error_payload
            except json.JSONDecodeError:
                detail = response.text
            raise ModelServiceError(
                f"{self.provider} HTTP {response.status_code}: {str(detail)[:1000]}",
                retryable=response.status_code in transient_statuses,
            )
        try:
            result = response.json()
        except json.JSONDecodeError as exc:
            raise ModelRequestError(
                f"{self.provider} returned non-JSON: {response.text[:1000]}"
            ) from exc
        try:
            message = result["choices"][0]["message"]
            if not isinstance(message, dict):
                raise TypeError("message must be an object")
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelRequestError(
                f"{self.provider} returned an unexpected response: "
                + json.dumps(result, ensure_ascii=False)[:1000]
            ) from exc
        if result["choices"][0].get("finish_reason") == "length":
            raise ModelRequestError(
                f"{self.provider} response was truncated at the completion budget ({max_tokens}); "
                "the model did not finish its text or tool arguments."
            )
        return result

    def openrouter_chat(self, **kwargs: Any) -> dict[str, Any]:
        """Backward-compatible name for the shared Chat Completions method."""
        return self.chat(**kwargs)


def build_model_caller(
    provider: Provider,
    *,
    base_url: str | None = None,
    auth_source: str = "auto",
) -> ModelCaller:
    """Read the selected provider's credentials without exposing secret values."""
    if provider in {"openai", "openrouter"}:
        prefix = provider.upper()
        api_key = os.environ.get(f"{prefix}_API_KEY", "").strip()
        if not api_key:
            raise SystemExit(f"Missing {prefix}_API_KEY.")
        endpoint = (
            base_url or os.environ.get(f"{prefix}_BASE_URL")
            or ("https://api.openai.com/v1" if provider == "openai" else "https://openrouter.ai/api/v1")
        ).strip()
        return ModelCaller(
            provider, **{f"{provider}_api_key": api_key, f"{provider}_base_url": endpoint},
        )

    if provider != "anthropic":
        raise ValueError(f"Unsupported provider: {provider}")

    kwargs = _anthropic_kwargs(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        auth_token=os.environ.get("ANTHROPIC_AUTH_TOKEN"),
        base_url=(
            base_url
            or os.environ.get("ANTHROPIC_BASE_URL")
            or "https://api.anthropic.com"
        ),
        auth_source=auth_source,
    )
    return ModelCaller("anthropic", anthropic_client=anthropic.Anthropic(**kwargs))
