#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

case "${1:-}" in
  0917)
    source_run=bio_phys_30_gpt56sol
    run_name=bio_phys_replay_0917_gpt54_20260929
    seed=20260925
    ;;
  0921)
    source_run=bio_phys_30_gpt56sol_20260921
    run_name=bio_phys_replay_0921_gpt54_20260929
    seed=20260926
    ;;
  *)
    echo "Usage: bash replay_gpt54_20260929.sh {0917|0921} {dry-run|start}" >&2
    exit 2
    ;;
esac

case "${2:-}" in
  dry-run) set -- --dry-run ;;
  start)
    if [[ -e "outputs/$run_name" ]]; then
      set -- --resume
    else
      set --
    fi
    ;;
  *)
    echo "Usage: bash replay_gpt54_20260929.sh {0917|0921} {dry-run|start}" >&2
    exit 2
    ;;
esac

for subject in biology physics; do
  source_equations="outputs/$source_run/_checkpoints/$subject/round_001/gen0/Equations/$subject/equations.jsonl"
  if [[ ! -s "$source_equations" ]]; then
    echo "Missing source scenarios: $source_equations" >&2
    exit 1
  fi
done

set -a
source .env
set +a
: "${OPENAI_API_KEY:?Load the model service API key in .env}"
: "${OPENAI_BASE_URL:?Set the matching model service URL in .env}"
export SRBENCH_OPENAI_MAX_RETRIES=1

conda run -n srbench-agent python -m srbench generate \
  --subjects biology physics \
  --target-per-subject 30 --batch-size 30 --n-subfields 7 \
  --steps 5 --max-steps 5 --max-lineage-attempts 2 --max-rounds 10 \
  --n-total 5000 --seed "$seed" \
  --provider openai --model gpt-5.4 \
  --executor local --workers 1 --job-timeout 5400 \
  --on-request-error defer --max-consecutive-request-errors 6 \
  --reuse-from "outputs/$source_run" --run-name "$run_name" \
  "$@"
