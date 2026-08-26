#!/usr/bin/env bash
# Stage 1-3 gen0 equation generation for a fixed-taxonomy subject.
# Usage: run_gen0.sh <subject> <run-name> [--resume]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SUBJECT="${1:?usage: run_gen0.sh <subject> <run-name> [--resume]}"
RUN_NAME="${2:?missing run-name}"
shift 2
export ANTHROPIC_BASE_URL="${SRBENCH_PROXY_URL:-http://127.0.0.1:8801}"
export ANTHROPIC_AUTH_TOKEN="${ANTHROPIC_AUTH_TOKEN:-hyra-local-claude-proxy}"
unset ANTHROPIC_API_KEY OPENROUTER_API_KEY
exec python3 "${HERE}/auto_workflow.py" \
  --subject "$SUBJECT" \
  --scenarios "${SCENARIOS:-70}" \
  --n-subfields "${N_SUBFIELDS:-7}" \
  --subfield-source fixed \
  --provider anthropic \
  --model "${GEN_MODEL:-claude-opus-4-8}" \
  --seed "${SEED:-0}" \
  --run-name "$RUN_NAME" \
  "$@"
