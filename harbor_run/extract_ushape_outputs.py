#!/usr/bin/env python3
"""Extract every ushape trial's final artefact into a readable tree + score table.

The agent's submitted files live only inside ``verifier/test-stdout.txt``, fenced
by the ``---- LAW BEGIN/END ----`` / ``---- EXPLAIN BEGIN/END ----`` markers that
``tests/test.sh`` prints before scoring.  This pulls them back out as real files
next to the reward, and rescores every law against the holdout on a *fixed*
scale so the official R2 can be sanity-checked.

Usage: extract_ushape_outputs.py <jobs_dir> <out_dir>
"""

from __future__ import annotations

import csv
import importlib.util
import json
import re
import shutil
import statistics
import sys
from pathlib import Path

import numpy as np
import pandas as pd

JOBS = {"opus-4.8": "ushape_opus48", "haiku-4.5": "ushape_haiku45"}
TASK = Path("/data1/SRBench/outputs/harbor_tasks_ushape/"
            "SRBench0826_ai_scaling_u_shape_000")


def fenced(text: str, name: str) -> str | None:
    m = re.search(rf"^-+ {name} BEGIN -+$\n(.*?)^-+ {name} END -+$", text, re.S | re.M)
    return m.group(1) if m else None


def rescore(law_path: Path, test: pd.DataFrame, var_train: float) -> dict[str, float]:
    """Re-run a saved law against the holdout, on both the official and a fixed scale.

    The official metric divides by var(y_test); dividing the same SSE by the
    *train* variance instead gives a scale that cannot be inflated by a
    low-variance holdout.  Here the two nearly coincide (ratio ~1.01), which is
    itself the finding -- but computing both keeps the check honest.
    """
    try:
        spec = importlib.util.spec_from_file_location(f"law_{law_path.parent.name}", law_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        rows = test[["logC"]].to_dict(orient="records")
        pred = np.asarray([r["Brier"] if isinstance(r, dict) else r
                           for r in mod.law(rows)], dtype=float)
    except Exception as exc:  # a law that will not import is a real failure
        return {"error": str(exc)[:200]}

    y = test["Brier"].to_numpy(dtype=float)
    if not np.all(np.isfinite(pred)):
        return {"error": "non-finite predictions"}
    mse = float(np.mean((pred - y) ** 2))
    return {
        "recomputed_r2": 1.0 - mse / float(np.var(y)),
        "fixed_scale_r2": 1.0 - mse / var_train,
        "rmse": float(np.sqrt(mse)),
        "max_abs_err": float(np.max(np.abs(pred - y))),
    }


def main() -> int:
    jobs_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    train = pd.read_csv(TASK / "environment" / "train_data.csv")
    test = pd.read_csv(TASK / "tests" / "test_data.csv")
    var_train = float(np.var(train["Brier"].to_numpy(dtype=float)))

    rows: list[dict[str, object]] = []
    for model, job_name in JOBS.items():
        job = jobs_dir / job_name
        if not job.is_dir():
            print(f"[warn] missing job {job}", file=sys.stderr)
            continue
        for i, trial in enumerate(sorted(p for p in job.iterdir() if p.is_dir()), 1):
            rec: dict[str, object] = {"model": model, "trial": trial.name, "attempt": i}
            dest = out_dir / model / trial.name
            dest.mkdir(parents=True, exist_ok=True)

            reward_file = trial / "verifier" / "reward.txt"
            if reward_file.exists():
                rec["official_reward"] = float(reward_file.read_text().strip())
                (dest / "reward.txt").write_text(reward_file.read_text())
            else:
                rec["official_reward"] = None
                rec["status"] = "ERROR"

            stdout = trial / "verifier" / "test-stdout.txt"
            if stdout.exists():
                text = stdout.read_text(errors="replace")
                law, explain = fenced(text, "LAW"), fenced(text, "EXPLAIN")
                if law:
                    (dest / "law.py").write_text(law)
                if explain:
                    (dest / "explain.md").write_text(explain)
                shutil.copy(stdout, dest / "verifier_stdout.txt")
                if law:
                    rec.update(rescore(dest / "law.py", test, var_train))

            res = trial / "result.json"
            if res.exists():
                d = json.loads(res.read_text())
                ar = d.get("agent_result") or {}
                rec["cost_usd"] = ar.get("cost_usd")
                rec["n_input_tokens"] = ar.get("n_input_tokens")
                rec["n_output_tokens"] = ar.get("n_output_tokens")
                rec["started_at"], rec["finished_at"] = d.get("started_at"), d.get("finished_at")
                (dest / "trial_meta.json").write_text(json.dumps(rec, indent=2) + "\n")
            rec.setdefault("status", "scored")
            rows.append(rec)

    out_dir.mkdir(parents=True, exist_ok=True)
    cols = ["model", "trial", "attempt", "official_reward", "recomputed_r2",
            "fixed_scale_r2", "rmse", "max_abs_err", "cost_usd",
            "n_input_tokens", "n_output_tokens", "status", "error"]
    with (out_dir / "scores.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    summary = {"var_train": var_train, "var_test": float(np.var(test["Brier"])), "by_model": {}}
    for model in JOBS:
        got = [r for r in rows if r["model"] == model and r.get("official_reward") is not None]
        if not got:
            continue
        rw = sorted(float(r["official_reward"]) for r in got)
        costs = [r["cost_usd"] for r in got if r.get("cost_usd") is not None]
        summary["by_model"][model] = {
            "n_trials": len(got),
            "rewards": rw,
            "mean_reward": statistics.fmean(rw),
            "median_reward": statistics.median(rw),
            "min_reward": rw[0],
            "worst_case_rmse": max((float(r["rmse"]) for r in got if r.get("rmse") is not None),
                                   default=None),
            "total_cost_usd": sum(costs) if costs else None,
        }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
