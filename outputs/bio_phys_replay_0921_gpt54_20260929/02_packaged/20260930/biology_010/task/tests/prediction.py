"""Fresh-process-per-row law execution shared with the exported Harbor verifier.

This reproduces evaluation semantics; a local subprocess is not a security sandbox.
"""
from __future__ import annotations
import json
import math
import os
import random
import select
import signal
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PredictionResult:
    values: list[float | None]
    errors: list[dict]

    @property
    def ok(self):
        return not self.errors and all(value is not None for value in self.values)


def _identity():
    if not hasattr(os, "geteuid") or os.geteuid() != 0:
        return {}
    import pwd
    account = pwd.getpwnam("nobody")
    group = account.pw_gid
    if group < 0:
        import grp
        group = grp.getgrnam("nogroup").gr_gid
    return {"user": account.pw_uid, "group": group, "extra_groups": []}


def isolated_predictions(law_path, rows, target, *, row_timeout=15.0, seed=0, drop_privileges=False):
    """Fail explicitly on the first bad row; never score a surviving subset."""
    if not hasattr(os, "fork"):
        raise RuntimeError("row isolation requires POSIX fork (macOS/Linux or the Harbor container)")
    if not math.isfinite(row_timeout) or row_timeout <= 0:
        raise ValueError("row_timeout must be positive and finite")
    law_path = Path(law_path).resolve()
    if not law_path.is_file():
        raise FileNotFoundError(law_path)
    values = [None] * len(rows)
    errors = []
    order = list(range(len(rows)))
    (random.SystemRandom() if seed is None else random.Random(seed)).shuffle(order)
    supervisor = None
    current = None
    with tempfile.TemporaryDirectory(prefix="srbench-law-") as directory:
        if drop_privileges:
            os.chmod(directory, 0o755)
        try:
            supervisor = subprocess.Popen(
                [sys.executable, "-c", _SUPERVISOR, str(law_path), target, str(row_timeout)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, cwd=directory, start_new_session=True,
                env={"PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                     "PYTHONUNBUFFERED": "1", "PYTHONDONTWRITEBYTECODE": "1"},
                bufsize=1, **(_identity() if drop_privileges else {}))
            for current in order:
                supervisor.stdin.write(json.dumps(rows[current], allow_nan=False) + "\n")
                supervisor.stdin.flush()
                # Module imports can be slower than a single row; each actual
                # row still has the deadline enforced in the supervisor.
                ready, _, _ = select.select([supervisor.stdout], [], [], max(20.0, row_timeout + 5.0))
                if not ready:
                    raise RuntimeError("candidate supervisor timed out")
                line = supervisor.stdout.readline()
                if not line:
                    raise RuntimeError("candidate supervisor exited early")
                result = json.loads(line)
                if not result.get("ok"):
                    raise RuntimeError(str(result.get("error")))
                value = float(result["value"])
                if not math.isfinite(value):
                    raise ValueError("candidate returned NaN or Inf")
                values[current] = value
            supervisor.stdin.close()
            supervisor.wait(timeout=5)
            if supervisor.returncode:
                raise RuntimeError("candidate supervisor failed")
        except Exception as exc:
            errors.append({"row_index": current, "error": f"{type(exc).__name__}: {exc}"})
        finally:
            if supervisor is not None:
                try:
                    os.killpg(supervisor.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                supervisor.wait()
                for stream in (supervisor.stdin, supervisor.stdout):
                    if stream is not None:
                        try:
                            stream.close()
                        except BrokenPipeError:
                            pass
    return PredictionResult(values, errors)

_SUPERVISOR = '\nimport contextlib, importlib.util, json, os, signal, sys, time\nlaw_path, target_name = sys.argv[1], sys.argv[2]\nrow_timeout = float(sys.argv[3])\ncontrol_fd = os.dup(0)\ncontrol = os.fdopen(control_fd, "r", encoding="utf-8")\nos.close(0)\nos.open(os.devnull, os.O_RDONLY)\ntry:\n    spec = importlib.util.spec_from_file_location("candidate_law", law_path)\n    module = importlib.util.module_from_spec(spec)\n    assert spec.loader is not None\n    with contextlib.redirect_stdout(sys.stderr):\n        spec.loader.exec_module(module)\n    law = module.law\nexcept BaseException as exc:\n    print(json.dumps({"ok": False, "error": "load: " + repr(exc)[:1000]}), flush=True)\n    raise SystemExit(0)\n\ndef predict_one(row):\n    read_fd, write_fd = os.pipe()\n    child = os.fork()\n    if child == 0:\n        os.close(read_fd)\n        os.close(control_fd)\n        try:\n            os.close(0)\n            os.open(os.devnull, os.O_RDONLY)\n            with contextlib.redirect_stdout(sys.stderr):\n                raw = law([row])\n            if not isinstance(raw, list) or len(raw) != 1:\n                raise ValueError("law([row]) must return exactly one prediction")\n            item = raw[0]\n            value = item[target_name] if isinstance(item, dict) else item\n            payload = {"ok": True, "value": float(value)}\n        except BaseException as exc:\n            payload = {"ok": False, "error": repr(exc)[:1000]}\n        try:\n            os.write(write_fd, json.dumps(payload, allow_nan=False).encode("utf-8"))\n        finally:\n            os.close(write_fd)\n        os._exit(0)\n    os.close(write_fd)\n    deadline = time.monotonic() + row_timeout\n    while True:\n        done, _ = os.waitpid(child, os.WNOHANG)\n        if done == child:\n            break\n        if time.monotonic() > deadline:\n            os.kill(child, signal.SIGKILL)\n            os.waitpid(child, 0)\n            os.close(read_fd)\n            return {"ok": False, "error": "candidate timed out on one hidden row"}\n        time.sleep(0.002)\n    chunks = []\n    while True:\n        chunk = os.read(read_fd, 65536)\n        if not chunk:\n            break\n        chunks.append(chunk)\n    os.close(read_fd)\n    try:\n        return json.loads(b"".join(chunks).decode("utf-8"))\n    except BaseException as exc:\n        return {"ok": False, "error": "child protocol: " + repr(exc)[:1000]}\n\nfor line in control:\n    try:\n        result = predict_one(json.loads(line))\n    except BaseException as exc:\n        result = {"ok": False, "error": "supervisor: " + repr(exc)[:1000]}\n    print(json.dumps(result, allow_nan=False), flush=True)\n'
