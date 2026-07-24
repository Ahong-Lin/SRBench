"""Small provider adapter shared by the non-Agent workflow stages.

Anthropic and OpenRouter expose different HTTP schemas even when both route to
the same underlying Claude model.  This module keeps that transport difference
outside the scientific workflow code.
"""

from __future__ import annotations

import json
import os
from typing import Any, Literal

import anthropic
import httpx


Provider = Literal["anthropic", "openrouter"]


class ModelRequestError(RuntimeError):
    """A compact, provider-neutral error for a failed model request."""


def _anthropic_kwargs(
    api_key: str | None,
    auth_token: str | None,
    base_url: str | None,
    auth_source: str,
) -> dict[str, str]:
    kwargs: dict[str, str] = {}
    if base_url:
        kwargs["base_url"] = base_url.strip()
    if auth_source == "api_key":
        if not api_key:
            raise SystemExit("Missing ANTHROPIC_API_KEY.")
        kwargs["api_key"] = api_key.strip()
        return kwargs
    if auth_source == "auth_token":
        if not auth_token:
            raise SystemExit("Missing ANTHROPIC_AUTH_TOKEN.")
        kwargs["auth_token"] = auth_token.strip()
        return kwargs
    if api_key:
        kwargs["api_key"] = api_key.strip()
        return kwargs
    if auth_token:
        kwargs["auth_token"] = auth_token.strip()
        return kwargs
    raise SystemExit("Missing ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN.")


class ModelCaller:
    """Make text or tool calls through Anthropic Messages or OpenRouter Chat API."""

    def __init__(
        self,
        provider: Provider,
        *,
        anthropic_client: anthropic.Anthropic | None = None,
        openrouter_api_key: str | None = None,
        openrouter_base_url: str | None = None,
    ) -> None:
        self.provider = provider
        self.anthropic_client = anthropic_client
        self.openrouter_api_key = openrouter_api_key
        self.openrouter_base_url = openrouter_base_url

    def complete(
        self,
        user_prompt: str,
        model: str,
        max_tokens: int,
        system_prompt: str | None = None,
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
        payload = self.openrouter_chat(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
        )
        content = payload.get("choices", [{}])[0].get("message", {}).get("content")
        if isinstance(content, list):
            content = "".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in content
            )
        if not isinstance(content, str) or not content.strip():
            raise ModelRequestError(
                "OpenRouter returned an empty or non-text response: "
                + json.dumps(payload, ensure_ascii=False)[:1000]
            )
        return content

    def openrouter_chat(
        self,
        *,
        messages: list[dict[str, Any]],
        model: str,
        max_tokens: int,
        tools: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Call OpenRouter's OpenAI-compatible Chat Completions endpoint."""
        if self.provider != "openrouter":
            raise ModelRequestError("Tool chat is only used by the OpenRouter provider.")
        if not self.openrouter_api_key or not self.openrouter_base_url:
            raise ModelRequestError("OpenRouter client was not initialized.")

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        endpoint = self.openrouter_base_url.rstrip("/") + "/chat/completions"
        try:
            response = httpx.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/llm-srbench",
                    "X-Title": "LLM-SRBench v5",
                },
                json=payload,
                timeout=120.0,
            )
        except httpx.HTTPError as exc:
            raise ModelRequestError(f"OpenRouter connection failed: {exc}") from exc
        if response.is_error:
            try:
                detail = response.json().get("error", response.text)
            except json.JSONDecodeError:
                detail = response.text
            raise ModelRequestError(
                f"OpenRouter HTTP {response.status_code}: {str(detail)[:1000]}"
            )
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise ModelRequestError(
                f"OpenRouter returned non-JSON: {response.text[:1000]}"
            ) from exc


def build_model_caller(
    provider: Provider,
    *,
    base_url: str | None = None,
    auth_source: str = "auto",
) -> ModelCaller:
    """Read the selected provider's credentials without exposing secret values."""
    if provider == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise SystemExit("Missing OPENROUTER_API_KEY.")
        return ModelCaller(
            "openrouter",
            openrouter_api_key=api_key.strip(),
            openrouter_base_url=(
                base_url
                or os.environ.get("OPENROUTER_BASE_URL")
                or "https://openrouter.ai/api/v1"
            ).strip(),
        )

    kwargs = _anthropic_kwargs(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
        auth_token=os.environ.get("ANTHROPIC_AUTH_TOKEN"),
        base_url=(
            base_url
            or os.environ.get("ANTHROPIC_BASE_URL")
            or "https://code.ppchat.vip/"
        ),
        auth_source=auth_source,
    )
    return ModelCaller("anthropic", anthropic_client=anthropic.Anthropic(**kwargs))
