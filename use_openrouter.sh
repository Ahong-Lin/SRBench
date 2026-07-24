#!/usr/bin/env zsh
# Configure the native OpenRouter provider used by v5.
# Source env.sh first, where OPENROUTER_API_KEY is defined.

if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
  echo "Missing OPENROUTER_API_KEY. Add it to env.sh, then source env.sh again." >&2
  return 1 2>/dev/null || exit 1
fi

# OpenRouter's official OpenAI-compatible endpoint is /api/v1/chat/completions.
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
export OPENROUTER_MODEL="${OPENROUTER_MODEL:-anthropic/claude-opus-4.8}"

echo "OpenRouter configured:"
echo "  base URL : $OPENROUTER_BASE_URL"
echo "  model    : $OPENROUTER_MODEL"
echo "  API key  : set"
