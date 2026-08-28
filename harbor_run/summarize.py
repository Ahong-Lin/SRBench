#!/usr/bin/env python3
"""Summarize a harbor SRbench job: per-task reward, cost, and failure triage.

Usage: python3 summarize.py <jobs_dir>/<job_name> [--csv out.csv]
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path


def load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("job_dir", type=Path)
    ap.add_argument("--csv", type=Path)
    args = ap.parse_args()

    rows = []
    for trial_dir in sorted(p for p in args.job_dir.iterdir() if p.is_dir()):
        res = load(trial_dir / "result.json")
        if res is None:
            continue
        # reward.txt is the task's own ground truth (R^2); result.json may round it.
        reward_txt = (trial_dir / "verifier" / "reward.txt")
        reward = None
        if reward_txt.exists():
            try:
                reward = float(reward_txt.read_text().strip())
            except ValueError:
                pass
        if reward is None:
            reward = (res.get("verifier_result") or {}).get("reward")
        ar = res.get("agent_result") or {}
        exc = res.get("exception_info")
        rows.append({
            "task": res.get("task_name") or trial_dir.name,
            "reward_r2": reward,
            "cost_usd": ar.get("cost_usd"),
            "in_tokens": ar.get("n_input_tokens"),
            "cache_tokens": ar.get("n_cache_tokens"),
            "out_tokens": ar.get("n_output_tokens"),
            "exception": (exc or {}).get("exception_type") if exc else "",
        })

    if not rows:
        print(f"no trials found under {args.job_dir}")
        return 1

    scored = [r["reward_r2"] for r in rows if isinstance(r["reward_r2"], (int, float))]
    costs = [r["cost_usd"] for r in rows if isinstance(r["cost_usd"], (int, float))]
    errs = [r for r in rows if r["exception"]]

    print(f"trials:        {len(rows)}")
    print(f"scored:        {len(scored)}")
    print(f"errored:       {len(errs)}")
    if scored:
        print(f"mean R2:       {statistics.fmean(scored):.4f}")
        print(f"median R2:     {statistics.median(scored):.4f}")
        for thr in (0.99, 0.9, 0.5, 0.0):
            n = sum(1 for s in scored if s >= thr)
            print(f"  R2 >= {thr:<4}   {n:>3}/{len(scored)}  ({n / len(scored):.0%})")
    if costs:
        print(f"total cost:    ${sum(costs):.2f}   (mean ${statistics.fmean(costs):.3f}/task)")

    print("\nworst 10 by R2:")
    for r in sorted((r for r in rows if isinstance(r["reward_r2"], (int, float))),
                    key=lambda r: r["reward_r2"])[:10]:
        print(f"  {r['reward_r2']:>10.4f}  {r['task']}")

    if errs:
        print("\nerrored trials:")
        for r in errs:
            print(f"  {r['exception']:<28} {r['task']}")

    if args.csv:
        with args.csv.open("w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        print(f"\nwrote {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
