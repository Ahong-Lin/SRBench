#!/usr/bin/env bash
# Run ONE SRBench v6 candidate end to end:
#   gen0 -> evolve >= STEPS gens -> novelty_check (repeat to MAX_STEPS until Yes)
#   -> DataSpec agent -> single N_TOTAL-point CSV.
# No Harbor task, no solver, no R^2 -- that is what --mode candidate means.
#
# Usage: run_candidate.sh <equations.jsonl> <scenario_id> <discipline> [extra args...]
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="${1:?usage: run_candidate.sh <equations.jsonl> <scenario_id> <discipline> [extra...]}"
SCENARIO_ID="${2:?missing scenario_id}"
DISCIPLINE="${3:?missing discipline}"
shift 3

# All three LLM stages (evolve, novelty, DataSpec) run on opus-4.8 through the
# local Anthropic-native proxy; the OpenAI gateway 429s too hard for a batch.
export ANTHROPIC_BASE_URL="${SRBENCH_PROXY_URL:-http://127.0.0.1:8801}"
export ANTHROPIC_AUTH_TOKEN="${ANTHROPIC_AUTH_TOKEN:-hyra-local-claude-proxy}"
unset ANTHROPIC_API_KEY OPENROUTER_API_KEY
# The DataSpec stage's Agent SDK spawns a binary named exactly `claude`.
export PATH="${HERE}/bin:${PATH}"

exec python3 "${HERE}/evolution_pipeline.py" \
  --input "$INPUT" \
  --id "$SCENARIO_ID" \
  --discipline "$DISCIPLINE" \
  --mode candidate \
  --steps "${STEPS:-5}" \
  --max-steps "${MAX_STEPS:-15}" \
  --max-lineage-attempts "${MAX_LINEAGE_ATTEMPTS:-4}" \
  --n-total "${N_TOTAL:-5000}" \
  --provider anthropic \
  --model "${GEN_MODEL:-claude-opus-4-8}" \
  --cli-path "${HERE}/bin/claude" \
  --output-dir "${OUTPUT_DIR:-${HERE}/outputs/Candidate_Equations}" \
  "$@"
