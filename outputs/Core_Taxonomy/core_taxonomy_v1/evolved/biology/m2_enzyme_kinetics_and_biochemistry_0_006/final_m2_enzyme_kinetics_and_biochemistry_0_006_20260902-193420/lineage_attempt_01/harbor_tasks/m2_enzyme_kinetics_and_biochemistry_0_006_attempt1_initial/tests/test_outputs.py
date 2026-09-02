"""Harbor verifier template for isolated, pointwise symbolic regression."""
from __future__ import annotations

import grp
import importlib.util
import json
import os
import pwd
import random
import select
import secrets
import signal
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

LAW_PATH = Path("/app/law.py")
TEST_DATA_PATH = Path("/tests/test_data.csv")
REWARD_OUTPUT_FILE = Path("/logs/verifier/reward.txt")

# Rewritten by harbor.build_task() for each task.
FEATURE_NAMES = ['pH', 'Temp']
TARGET_NAME = 'A'

# Candidate code is imported without the hidden CSV present. Every row is then
# evaluated in a fresh fork, so no cross-row state or trajectory can leak.
_SUPERVISOR = r'''
import contextlib, importlib.util, json, os, signal, sys, time
law_path, target_name = sys.argv[1], sys.argv[2]
control_fd = os.dup(0)
control = os.fdopen(control_fd, "r", encoding="utf-8")
os.close(0)
os.open(os.devnull, os.O_RDONLY)
try:
    spec = importlib.util.spec_from_file_location("candidate_law", law_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    with contextlib.redirect_stdout(sys.stderr):
        spec.loader.exec_module(module)
    law = module.law
except BaseException as exc:
    print(json.dumps({"ok": False, "error": "load: " + repr(exc)}), flush=True)
    raise SystemExit(0)

def predict_one(row):
    read_fd, write_fd = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(read_fd)
        os.close(control_fd)
        try:
            os.close(0)
            os.open(os.devnull, os.O_RDONLY)
            with contextlib.redirect_stdout(sys.stderr):
                raw = law([row])
            if not isinstance(raw, list) or len(raw) != 1:
                raise ValueError("law([row]) must return exactly one prediction")
            item = raw[0]
            value = item[target_name] if isinstance(item, dict) else item
            payload = {"ok": True, "value": float(value)}
        except BaseException as exc:
            payload = {"ok": False, "error": repr(exc)}
        try:
            os.write(write_fd, json.dumps(payload, allow_nan=False).encode("utf-8"))
        finally:
            os.close(write_fd)
        os._exit(0)
    os.close(write_fd)
    deadline = time.monotonic() + 15.0
    while True:
        done, _ = os.waitpid(child, os.WNOHANG)
        if done == child:
            break
        if time.monotonic() > deadline:
            os.kill(child, signal.SIGKILL)
            os.waitpid(child, 0)
            os.close(read_fd)
            return {"ok": False, "error": "candidate timed out on one hidden row"}
        time.sleep(0.002)
    chunks = []
    while True:
        chunk = os.read(read_fd, 65536)
        if not chunk:
            break
        chunks.append(chunk)
    os.close(read_fd)
    try:
        return json.loads(b"".join(chunks).decode("utf-8"))
    except BaseException as exc:
        return {"ok": False, "error": "child protocol: " + repr(exc)}

for line in control:
    try:
        result = predict_one(json.loads(line))
    except BaseException as exc:
        result = {"ok": False, "error": "supervisor: " + repr(exc)}
    print(json.dumps(result, allow_nan=False), flush=True)
'''

def _candidate_identity() -> dict[str, int | list[int]]:
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        return {}
    try:
        account = pwd.getpwnam("nobody")
        group_id = account.pw_gid
        if group_id < 0:
            group_id = grp.getgrnam("nogroup").gr_gid
        return {"user": account.pw_uid, "group": group_id, "extra_groups": []}
    except KeyError:
        return {}

def isolated_predictions(rows: list[dict[str, float]]) -> list[float]:
    hidden_stash: Path | None = None
    supervisor: subprocess.Popen[str] | None = None
    try:
        if TEST_DATA_PATH.exists():
            hidden_stash = TEST_DATA_PATH.with_name("." + TEST_DATA_PATH.name + ".verifier-" + secrets.token_hex(12))
            os.replace(TEST_DATA_PATH, hidden_stash)
            os.chmod(hidden_stash, 0o600)
        supervisor = subprocess.Popen(
            [sys.executable, "-c", _SUPERVISOR, str(LAW_PATH), TARGET_NAME],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, cwd="/tmp",
            env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"), "PYTHONUNBUFFERED": "1"},
            bufsize=1, **_candidate_identity())
        assert supervisor.stdin is not None and supervisor.stdout is not None
        order = list(range(len(rows)))
        random.SystemRandom().shuffle(order)
        predictions: list[float | None] = [None] * len(rows)
        for index in order:
            supervisor.stdin.write(json.dumps(rows[index], allow_nan=False) + "\n")
            supervisor.stdin.flush()
            ready, _, _ = select.select([supervisor.stdout], [], [], 20.0)
            if not ready:
                raise RuntimeError("candidate supervisor timed out")
            line = supervisor.stdout.readline()
            if not line:
                raise RuntimeError("candidate supervisor exited early")
            result = json.loads(line)
            if not result.get("ok"):
                raise RuntimeError("candidate failed: " + str(result.get("error")))
            predictions[index] = float(result["value"])
        supervisor.stdin.close()
        supervisor.wait(timeout=30)
        if supervisor.returncode:
            raise RuntimeError("candidate supervisor failed")
        return [float(value) for value in predictions]
    finally:
        if supervisor is not None and supervisor.poll() is None:
            supervisor.kill()
            supervisor.wait()
        if hidden_stash is not None and hidden_stash.exists() and not TEST_DATA_PATH.exists():
            os.replace(hidden_stash, TEST_DATA_PATH)

def calculate_metrics(predictions: list[float], true_values: list[float]) -> tuple[float, float, float]:
    pred = np.asarray(predictions, dtype=float)
    truth = np.asarray(true_values, dtype=float)
    if np.any(~np.isfinite(pred)):
        raise ValueError("predictions contain NaN or Inf")
    variance = float(np.var(truth))
    if variance < 1e-12:
        raise ValueError("hidden target variance is near zero; R² is undefined")
    mse = float(np.mean((pred - truth) ** 2))
    mad = float(np.mean(np.abs(truth - np.mean(truth))))
    if mad < 1e-12:
        raise ValueError("hidden target MAD is near zero")
    return mse / variance, float(np.mean(np.abs(pred - truth))) / mad, 1.0 - mse / variance

def write_reward(value: float) -> None:
    REWARD_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    REWARD_OUTPUT_FILE.write_text(f"{value:.6f}\n", encoding="utf-8")
    print(f"[INFO] Reward written to {REWARD_OUTPUT_FILE}: {value:.6f}")

def main() -> None:
    try:
        if not LAW_PATH.exists():
            raise FileNotFoundError(f"{LAW_PATH} not found")
        frame = pd.read_csv(TEST_DATA_PATH)
        required = [*FEATURE_NAMES, TARGET_NAME]
        missing = [name for name in required if name not in frame.columns]
        if missing:
            raise ValueError("hidden data lacks: " + ", ".join(missing))
        predictions = isolated_predictions(frame[FEATURE_NAMES].to_dict(orient="records"))
        nmse, nmae, r2 = calculate_metrics(predictions, frame[TARGET_NAME].tolist())
    except Exception as exc:
        print(f"[ERROR] Evaluation failed: {exc}")
        write_reward(-1.0)
        raise SystemExit(1)
    print("Evaluation Results (isolated single-row law([row]) calls):")
    print(f"  NMSE: {nmse:.6f}\n  NMAE: {nmae:.6f}\n  R²:   {r2:.6f}")
    write_reward(r2)

if __name__ == "__main__":
    main()
