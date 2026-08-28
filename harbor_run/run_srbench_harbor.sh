#!/usr/bin/env bash
# Run the 67 SRbench_8_6 harbor tasks locally in Docker on opus-4.8, via the
# app-id:app-key gateway (hyra's Anthropic-compat proxy in front of it).
#
# Verified live before this script existed:
#   * container -> 172.17.0.1:PORT reaches a host-bound listener from a container on a
#     CUSTOM compose bridge (172.18/16), which is harbor's actual per-trial topology.
#     host.docker.internal does NOT resolve here (native Engine, no extra_hosts).
#   * proxy -> gateway -> opus-4.8 round-trips (2.2s, "PROXY_OK")
#   * harbor discovers exactly 67 tasks from the parent dir (n_total_trials: 67)
#   * 5 full trials: R2 = 1.0 / 1.0 / 1.0 / 0.9997 / 0.996, $0.21-$0.51 each, ~2 min each
#
# Usage:
#   ./run_srbench_harbor.sh                 # all 67 on opus-4.8, default concurrency
#   N_CONCURRENT=4 ./run_srbench_harbor.sh  # override concurrency
#   LIMIT=5 ./run_srbench_harbor.sh         # first 5 tasks only (rehearsal)
#
#   # haiku 4.5 (iwiki.woa.com/p/4018838598) -- own port so both can run side by side.
#   # EFFORT is auto-empty for this preset: no extended thinking, and its gateway 400s
#   # on output_config.effort.
#   PRESET=haiku-4.5 MODEL=claude-haiku-4-5 PROXY_PORT=8789 \
#     STATEFILE=/tmp/srbench_haiku_proxy.json JOB_NAME=srbench86_haiku45_full \
#     ./run_srbench_harbor.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TASKS_DIR="${TASKS_DIR:-/tmp/srb86/outputs/SRbench_8_6}"
JOBS_DIR="${JOBS_DIR:-/data1/SRBench/outputs/harbor_jobs}"
JOB_NAME="${JOB_NAME:-srbench86_opus48_$(date +%Y%m%d_%H%M%S)}"
PRESET="${PRESET:-opus-4.8}"
PROXY_PORT="${PROXY_PORT:-8788}"
STATEFILE="${STATEFILE:-/tmp/srbench_harbor_proxy.json}"

# Concurrency. Binding constraint is RAM, not cores: each trial holds a container
# (python+numpy/scipy fit) plus a node `claude` CLI, and the 2048MB task limit is a
# cap rather than a reservation. 6 leaves the box usable; disk stays flat because all
# 67 images share the same python:3.12-slim + pip layers.
N_CONCURRENT="${N_CONCURRENT:-6}"
N_ATTEMPTS="${N_ATTEMPTS:-1}"
MODEL="${MODEL:-claude-opus-4-8}"
# Reasoning effort maps to the CLI's --effort flag. Leave EFFORT empty for models
# without extended thinking (e.g. haiku-4.5): its gateway rejects output_config.effort
# with HTTP 400 "Extra inputs are not permitted".
case "$PRESET" in
  haiku-4.5) EFFORT="${EFFORT-}" ;;
  *)         EFFORT="${EFFORT-high}" ;;
esac

# --- disk guard ------------------------------------------------------------
# Docker root lives on / here; a full / breaks the daemon AND the host.
DOCKER_ROOT="$(docker info --format '{{.DockerRootDir}}' 2>/dev/null || echo /var/lib/docker)"
AVAIL_MB=$(df -Pm "$DOCKER_ROOT" | awk 'NR==2{print $4}')
if (( AVAIL_MB < 6000 )); then
  echo "ABORT: only ${AVAIL_MB}MB free on docker root ($DOCKER_ROOT); need >=6000MB." >&2
  echo "Reclaim with: docker system prune -af   (frees ~35GB of stale images here)" >&2
  exit 1
fi
echo "[disk] ${AVAIL_MB}MB free on $DOCKER_ROOT"

# --- proxy -----------------------------------------------------------------
# One long-lived proxy for the whole run. Reused if already listening.
if curl -sf -m 3 -o /dev/null "http://127.0.0.1:${PROXY_PORT}/" 2>/dev/null \
   || (exec 3<>/dev/tcp/127.0.0.1/${PROXY_PORT}) 2>/dev/null; then
  echo "[proxy] reusing listener on 127.0.0.1:${PROXY_PORT}"
else
  echo "[proxy] starting ${PRESET} on 0.0.0.0:${PROXY_PORT}"
  nohup python3 "${HERE}/proxy_daemon.py" --preset "$PRESET" --port "$PROXY_PORT" \
      --statefile "$STATEFILE" > "/tmp/srbench_proxy_${PRESET}.log" 2>&1 &
  echo $! > "/tmp/srbench_proxy_${PRESET}.pid"
  sleep 6
fi

CONTAINER_URL="$(python3 -c "import json;print(json.load(open('$STATEFILE'))['container_url'])")"
SENTINEL="$(python3 -c "import json;print(json.load(open('$STATEFILE'))['sentinel_api_key'])")"
echo "[proxy] container_url=$CONTAINER_URL"

# Fail fast if the gateway is not actually answering -- cheaper than 67 dead trials.
# Sends the same shape Claude Code does (stream + thinking), so a model-contract
# mismatch surfaces here rather than as 67 UnknownApiError trials.
python3 - "$CONTAINER_URL" "$SENTINEL" "$MODEL" <<'PY'
import json, sys, urllib.request
url, key, model = sys.argv[1], sys.argv[2], sys.argv[3]
# The gateway now rejects thinking.type=enabled ("use adaptive and
# output_config.effort"), so preflight with adaptive; falling back to no thinking
# block keeps presets without extended thinking (haiku-4.5) working.
body = {"model": model, "max_tokens": 4096,
        "thinking": {"type": "adaptive"},
        "messages": [{"role": "user", "content": "Reply with exactly: READY"}]}


def ask(payload):
    req = urllib.request.Request(url.rstrip("/") + "/v1/messages", data=json.dumps(payload).encode(),
        method="POST", headers={"Content-Type": "application/json", "x-api-key": key,
                                "anthropic-version": "2023-06-01"})
    return json.loads(urllib.request.urlopen(req, timeout=180).read().decode())


try:
    d = ask(body)
except Exception as exc:
    print(f"[preflight] adaptive thinking rejected ({exc}); retrying without a thinking block")
    d = ask({k: v for k, v in body.items() if k != "thinking"})
txt = "".join(b.get("text", "") for b in d.get("content", []) if b.get("type") == "text")
print(f"[preflight] model={d.get('model')} reply={txt.strip()!r}")
assert "READY" in txt, "gateway did not answer as expected"
PY

# --- the run ---------------------------------------------------------------
# ANTHROPIC_BASE_URL must be in the ORCHESTRATOR's env, not only in --ae:
# claude_code.py:1393 reads it from os.environ, and that read is what gates the
# ANTHROPIC_DEFAULT_{OPUS,SONNET,HAIKU}_MODEL / subagent-model aliasing at :1460.
# --ae carries it into the container; the export makes the aliasing fire.
export ANTHROPIC_BASE_URL="$CONTAINER_URL"
export ANTHROPIC_API_KEY="$SENTINEL"
# Clear ambient vars that would otherwise win. A stale ANTHROPIC_BASE_URL (e.g. this
# session's own 127.0.0.1 proxy) would be baked into every container, where loopback is
# the container's own empty loopback; and claude_code.py:1379-81 falls back to
# ANTHROPIC_AUTH_TOKEN for the key. Also drop model pins so -m wins.
unset ANTHROPIC_AUTH_TOKEN CLAUDE_CODE_OAUTH_TOKEN ANTHROPIC_MODEL \
      ANTHROPIC_DEFAULT_OPUS_MODEL ANTHROPIC_DEFAULT_SONNET_MODEL \
      ANTHROPIC_DEFAULT_HAIKU_MODEL CLAUDE_CODE_SUBAGENT_MODEL \
      CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY 2>/dev/null || true

mkdir -p "$JOBS_DIR"

ARGS=(
  -p "$TASKS_DIR"
  -a claude-code -m "$MODEL"
  -e docker
  --ae ANTHROPIC_BASE_URL="$CONTAINER_URL"
  --ae ANTHROPIC_API_KEY="$SENTINEL"
  --ae CLAUDE_CODE_MAX_RETRIES=4
  -k "$N_ATTEMPTS" -n "$N_CONCURRENT"
  -o "$JOBS_DIR" --job-name "$JOB_NAME"
  -y
)
[[ -n "$EFFORT" ]] && ARGS+=(--ak "reasoning_effort=${EFFORT}")
# No -r / --retry-exclude on purpose. cli/jobs.py:1230 ASSIGNS (not unions) the
# exclude set, so passing any --retry-exclude would drop the 9 sane defaults in
# models/job/config.py:288-302 -- making AgentAuthenticationError and
# RewardFileNotFoundError retryable, i.e. paying 3x for a failure a retry can't fix.
[[ -n "${LIMIT:-}" ]] && ARGS+=(-l "$LIMIT")

echo "[run] harbor run ${ARGS[*]}"
# Never wrap this in `timeout`: harbor records CancelledError, scores the trial 0,
# and discards agent output that was already written. Tasks declare their own
# agent.timeout_sec = 3600; let harbor enforce it.
harbor run "${ARGS[@]}"

echo
echo "[done] results: ${JOBS_DIR}/${JOB_NAME}/result.json"
echo "[done] summarize: python3 ${HERE}/summarize.py ${JOBS_DIR}/${JOB_NAME}"
