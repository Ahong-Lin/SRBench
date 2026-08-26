#!/usr/bin/env python3
"""Report candidate-generation progress and classify every failure by stage.

Reads outputs/Candidate_Equations plus the per-scenario batch logs, so it works
while the batch is still running.
"""
from __future__ import annotations

import collections
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent
CAND = ROOT / "outputs" / "Candidate_Equations"
RUNS = {
    "physics": "physics_fixed_main",
    "biology": "biology_fixed_main",
    "AI": "AI_fixed_main",
}


def gen0_ids(run: str) -> list[str]:
    path = ROOT / "outputs" / "Equations" / run / "equations.jsonl"
    if not path.exists():
        return []
    out = []
    for line in path.open():
        rec = json.loads(line)
        if rec.get("expression"):
            out.append(rec["scenario_id"])
    return out


def candidate_dirs() -> dict[str, list[pathlib.Path]]:
    """Map scenario_id -> its candidate directories (a retry adds another)."""
    by_id: dict[str, list[pathlib.Path]] = collections.defaultdict(list)
    for d in sorted(CAND.glob("candidate_*")):
        by_id[d.name.removeprefix("candidate_").rsplit("_", 1)[0]].append(d)
    return by_id


def classify(scenario_id: str, discipline: str, dirs: list[pathlib.Path]) -> dict:
    """Name the stage a failed scenario stopped at, and why."""
    log = ROOT / "runlogs" / "batch" / discipline / f"{scenario_id}.log"
    text = log.read_text(errors="replace") if log.exists() else ""
    attempts = []
    for d in dirs:
        audit = d / "lineage_attempts.jsonl"
        if audit.exists():
            attempts += [json.loads(l) for l in audit.open()]

    statuses = [a.get("status") for a in attempts]
    errors = [a.get("error") for a in attempts if a.get("error")]
    novelty_no = sum(1 for s in statuses if s == "reject_not_novel")

    if errors:
        stage = "DataSpec/data-generation" if any(
            k in errors[-1] for k in ("SpecAgentError", "spec", "Spec")
        ) else "evolve/pipeline"
        detail = errors[-1]
    elif novelty_no and not any(s == "candidate_generated" for s in statuses):
        stage, detail = "novelty_check", (
            f"{novelty_no} lineage attempt(s) judged not novel; "
            "max-lineage-attempts exhausted"
        )
    elif "Traceback" in text:
        stage = "process crash"
        detail = text.strip().splitlines()[-1][:300]
    elif not dirs:
        stage, detail = "not started / no output dir", "no candidate directory"
    else:
        stage, detail = "unknown", (text.strip().splitlines() or ["(no log)"])[-1][:300]
    return {
        "id": scenario_id, "discipline": discipline, "stage": stage,
        "error": detail, "attempts": len(attempts), "statuses": statuses,
        "dirs": [str(d.relative_to(ROOT)) for d in dirs],
    }


def main() -> int:
    running = "--running" in sys.argv
    report: dict[str, dict] = {}
    for discipline, run in RUNS.items():
        ids = gen0_ids(run)
        by_id = candidate_dirs()
        ok, failed, pending = [], [], []
        for scenario_id in ids:
            dirs = by_id.get(scenario_id, [])
            if any((d / "final_spec.json").exists() for d in dirs):
                ok.append(scenario_id)
            elif dirs or (ROOT / "runlogs" / "batch" / discipline /
                          f"{scenario_id}.log").exists():
                # A live run also has a dir but no final_spec yet.
                log = ROOT / "runlogs" / "batch" / discipline / f"{scenario_id}.log"
                text = log.read_text(errors="replace") if log.exists() else ""
                if running and "No acceptable final" not in text and "Traceback" not in text:
                    pending.append(scenario_id)
                else:
                    failed.append(classify(scenario_id, discipline, dirs))
            else:
                pending.append(scenario_id)
        report[discipline] = {
            "gen0": len(ids), "candidates_ok": len(ok),
            "failed": failed, "pending": pending,
            "ok_ids": ok,
        }
        print(f"{discipline:8s} gen0={len(ids):3d}  candidates={len(ok):3d}  "
              f"failed={len(failed):3d}  pending={len(pending):3d}")
    (ROOT / "runlogs" / "progress.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    total_ok = sum(r["candidates_ok"] for r in report.values())
    total_gen0 = sum(r["gen0"] for r in report.values())
    print(f"{'TOTAL':8s} gen0={total_gen0:3d}  candidates={total_ok:3d}")
    for discipline, r in report.items():
        for f in r["failed"]:
            print(f"  FAIL [{discipline}] {f['id']}: {f['stage']} :: {f['error'][:160]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
