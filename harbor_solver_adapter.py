"""Run one Harbor SR task and expose its verifier R² to evolution_pipeline.py.

This is intentionally a thin adapter.  Harbor remains responsible for executing
the selected coding agent and the task's hidden-data verifier; this script only
waits for the job, locates its reward.txt, and prints the JSON contract expected
by ``evolution_pipeline.py``.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


def _latest_reward(jobs_dir: Path) -> Path:
    rewards = sorted(jobs_dir.glob("**/verifier/reward.txt"), key=lambda p: p.stat().st_mtime)
    if not rewards:
        raise FileNotFoundError(f"Harbor produced no verifier reward.txt below {jobs_dir}")
    return rewards[-1]


def main() -> None:
    p = argparse.ArgumentParser(description="Run one Harbor task and print its raw verifier test R² as JSON.")
    p.add_argument("--task", required=True, type=Path, help="Harbor-format task directory")
    p.add_argument("--harbor-bin", default="harbor")
    p.add_argument("--agent", default="claude-code")
    p.add_argument("--model", required=True, help="e.g. claude-opus-4-8 or gpt-5.6-sol")
    p.add_argument("--env", default="daytona")
    p.add_argument("--job-name", default="srbench_difficulty_gate")
    p.add_argument("--extra", action="append", default=[], help="one extra Harbor CLI argument; repeat as needed")
    args = p.parse_args()
    task = args.task.resolve()
    if not (task / "task.toml").exists():
        raise SystemExit(f"not a Harbor task: {task}")
    jobs = task / "harbor_jobs"
    command = [args.harbor_bin, "run", "-p", str(task), "-a", args.agent, "-m", args.model,
               "--env", args.env, "--job-name", args.job_name, "--jobs-dir", str(jobs), "--yes"]
    command.extend(args.extra)
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode:
        raise SystemExit(f"Harbor exited {completed.returncode}\n{completed.stderr[-3000:]}")
    reward = _latest_reward(jobs)
    try:
        raw = float(reward.read_text(encoding="utf-8").strip())
    except ValueError as exc:
        raise SystemExit(f"invalid Harbor reward file {reward}") from exc
    print(json.dumps({"raw_test_r2": raw, "harbor_task": str(task),
                      "harbor_reward": str(reward), "harbor_stdout": completed.stdout[-4000:]}))


if __name__ == "__main__":
    main()
