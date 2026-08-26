#!/usr/bin/env bash
# Fan run_candidate.sh out over every gen0 equation in one subject's
# equations.jsonl, WORKERS at a time. Each candidate writes its own timestamped
# directory, so concurrent runs never touch the same file.
#
# Already-finished scenario_ids are skipped, which makes this re-runnable: kill
# it, fix whatever broke, start it again and it tops up the gaps.
#
# Usage: run_candidate_batch.sh <equations.jsonl> <discipline> <logdir>
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INPUT="${1:?usage: run_candidate_batch.sh <equations.jsonl> <discipline> <logdir>}"
DISCIPLINE="${2:?missing discipline}"
LOGDIR="${3:?missing logdir}"
WORKERS="${WORKERS:-6}"
OUT_ROOT="${OUTPUT_DIR:-${HERE}/outputs/Candidate_Equations}"
mkdir -p "$LOGDIR"

mapfile -t IDS < <(python3 - "$INPUT" "$OUT_ROOT" <<'PY'
import json, pathlib, sys
equations, out_root = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
ids = [json.loads(l)["scenario_id"] for l in equations.open()
       if json.loads(l).get("expression")]
# A candidate counts as done only once final_spec.json exists; a directory left
# behind by a crashed run must not mask a missing candidate.
done = {p.parent.name.removeprefix("candidate_").rsplit("_", 1)[0]
        for p in out_root.glob("candidate_*/final_spec.json")}
for scenario_id in ids:
    if scenario_id not in done:
        print(scenario_id)
PY
)

echo "[$DISCIPLINE] ${#IDS[@]} candidate(s) to run, ${WORKERS} at a time" >&2
if [ "${#IDS[@]}" -eq 0 ]; then exit 0; fi

printf '%s\n' "${IDS[@]}" | xargs -P "$WORKERS" -I{} \
  bash -c '"$0"/run_candidate.sh "$1" "{}" "$2" > "$3/{}.log" 2>&1; \
           printf "%s %s\n" "$([ $? -eq 0 ] && echo OK || echo FAIL)" "{}" >&2' \
  "$HERE" "$INPUT" "$DISCIPLINE" "$LOGDIR"
