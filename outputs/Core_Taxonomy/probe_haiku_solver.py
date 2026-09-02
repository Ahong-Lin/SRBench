#!/usr/bin/env python3
"""Re-score core_taxonomy_v1's already-evaluated Harbor tasks with haiku-4.5.

Purpose: the opus run's first nine Harbor evaluations all came back R² > 0.90
(median exactly 1.0000), so every gen0 was eliminated by rule 7.  That single
number cannot distinguish two very different explanations:

  (a) the generated tasks are too easy — any competent solver saturates them; or
  (b) opus-4.8 is simply a very strong solver on tasks that are otherwise fine.

Running a weaker solver (haiku-4.5) over the SAME Harbor tasks separates the two.
If haiku also lands near 1.0, the tasks are too easy and the difficulty gate needs
harder generation.  If haiku falls well below 0.90, the tasks carry real
difficulty and the gate is really measuring solver strength.

**This is a diagnostic probe, not part of the official experiment.**  It never
touches ``core_taxonomy_v1``'s ledger or its Harbor task directories: each task is
copied to a scratch tree first, so the official one-shot record (rule 2: at most
one Harbor evaluation per gen0) stays intact and auditable.

Usage: probe_haiku_solver.py [--limit N]
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

RUN = Path("/data1/SRBench/outputs/Core_Taxonomy/core_taxonomy_v1")
PROBE = Path("/data1/SRBench/outputs/Core_Taxonomy/haiku_solver_probe")
PROXY_STATE = Path("/tmp/srbench_haiku_proxy.json")


def opus_scored_tasks() -> list[dict[str, object]]:
    """Every Harbor task in the official run that already has a reward."""
    found = []
    for reward in RUN.glob("evolved/**/harbor_jobs/**/verifier/reward.txt"):
        # .../harbor_tasks/<task>/harbor_jobs/<job>/<trial>/verifier/reward.txt
        task_dir = reward
        while task_dir.name != "harbor_jobs" and task_dir != task_dir.parent:
            task_dir = task_dir.parent
        task_dir = task_dir.parent
        if not (task_dir / "task.toml").exists():
            continue
        try:
            opus_r2 = float(reward.read_text(encoding="utf-8").strip())
        except ValueError:
            continue
        # equation id is the directory under evolved/<subject>/
        parts = task_dir.relative_to(RUN / "evolved").parts
        found.append({"subject": parts[0], "equation_id": parts[1],
                      "task": task_dir, "opus_r2": opus_r2})
    # De-duplicate by equation id, keeping the first (one-shot means one task each).
    seen: set[str] = set()
    unique = []
    for item in sorted(found, key=lambda d: str(d["equation_id"])):
        if item["equation_id"] in seen:
            continue
        seen.add(str(item["equation_id"]))
        unique.append(item)
    return unique


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    if not PROXY_STATE.exists():
        print(f"missing haiku proxy statefile {PROXY_STATE}", file=sys.stderr)
        return 1
    state = json.loads(PROXY_STATE.read_text())
    sentinel, container_url = state["sentinel_api_key"], state["container_url"]

    tasks = opus_scored_tasks()
    if args.limit:
        tasks = tasks[: args.limit]
    if not tasks:
        print("no scored Harbor tasks found in the official run", file=sys.stderr)
        return 1

    PROBE.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, item in enumerate(tasks, 1):
        eid = str(item["equation_id"])
        # Copy so the official task tree and its one-shot reward are never touched.
        dest = PROBE / "tasks" / eid
        if dest.exists():
            shutil.rmtree(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(item["task"], dest, ignore=shutil.ignore_patterns("harbor_jobs"))

        cmd = ["python3", "-m", "harbor", "run", "--task", str(dest),
               "--model", "claude-haiku-4-5", "--agent", "claude-code",
               "--env", "docker", "--job-name", "haiku_solver_probe",
               f"--extra=--ae", f"--extra=ANTHROPIC_BASE_URL={container_url}",
               f"--extra=--ae", f"--extra=ANTHROPIC_API_KEY={sentinel}"]
        print(f"[{i}/{len(tasks)}] {eid} (opus R²={item['opus_r2']:.6f}) ...", flush=True)
        proc = subprocess.run(cmd, text=True, capture_output=True, cwd="/data1/SRBench")
        rec: dict[str, object] = {"equation_id": eid, "subject": item["subject"],
                                  "opus_r2": item["opus_r2"],
                                  "official_task": str(item["task"])}
        if proc.returncode:
            rec["haiku_r2"] = None
            rec["error"] = (proc.stderr or proc.stdout)[-600:]
            print(f"    FAILED rc={proc.returncode}", flush=True)
        else:
            try:
                payload = json.loads(proc.stdout.strip().splitlines()[-1])
                rec["haiku_r2"] = payload["raw_test_r2"]
                rec["haiku_reward_file"] = payload.get("harbor_reward")
                print(f"    haiku R²={rec['haiku_r2']:.6f}", flush=True)
            except Exception as exc:
                rec["haiku_r2"] = None
                rec["error"] = f"parse: {exc}; tail={proc.stdout[-400:]}"
                print("    could not parse harbor output", flush=True)
        rows.append(rec)
        (PROBE / "probe_results.json").write_text(json.dumps(rows, indent=2) + "\n")

    ok = [r for r in rows if r.get("haiku_r2") is not None]
    summary = {
        "n_tasks": len(rows),
        "n_scored": len(ok),
        "opus_median_r2": statistics.median([float(r["opus_r2"]) for r in rows]),
        "haiku_median_r2": statistics.median([float(r["haiku_r2"]) for r in ok]) if ok else None,
        "opus_n_le_0.90": sum(1 for r in rows if float(r["opus_r2"]) <= 0.90),
        "haiku_n_le_0.90": sum(1 for r in ok if float(r["haiku_r2"]) <= 0.90),
        "interpretation": (
            "haiku also near 1.0 => tasks too easy; haiku well below 0.90 => tasks "
            "carry real difficulty and the gate reflects solver strength"),
    }
    (PROBE / "probe_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
