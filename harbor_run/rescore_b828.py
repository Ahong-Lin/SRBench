#!/usr/bin/env python3
"""Re-score submitted b828 laws outside the container, to check the official rewards.

Every trial's reward came from the verifier running inside a throwaway container.
This re-executes each extracted ``law.py`` against the same holdout, under the same
metric, on the host -- so a reward that cannot be reproduced here means either the
law depends on container state or the reward is not what it claims.

Also reports a FIXED-SCALE R2 (dividing the same SSE by var(y_train) rather than
var(y_test)).  On this set 24 of 25 holdouts are right-extrapolation segments and
several have var_test/var_train below 1e-4, so the official R2 amplifies tiny
absolute errors into rewards like -2.5e8.  The fixed-scale number is the one to
compare across tasks.

Usage: rescore_b828.py [<outputs_dir>] [<tasks_dir>]
"""

from __future__ import annotations

import ast
import csv
import importlib.util
import json
import statistics
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

DEFAULT_OUT = Path("/data1/SRBench/harbor_run/b828_outputs")
DEFAULT_TASKS = Path("/data1/SRBench/outputs/harbor_tasks_b828")


def _one(law, row: dict[str, float], target: str) -> float:
    """Call law() the way the verifier does: a single row, returning one number."""
    out = law([row])
    if isinstance(out, (list, tuple)):
        if not out:
            raise ValueError("law returned an empty sequence for one row")
        first = out[0]
        return float(first[target] if isinstance(first, dict) else first)
    if isinstance(out, dict):
        return float(out[target])
    return float(out)


def verifier_contract(task: Path) -> tuple[list[str], str]:
    src = (task / "tests" / "test_outputs.py").read_text()
    feats: list[str] = []
    target = ""
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Assign):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name) and tgt.id == "FEATURE_NAMES":
                    try:
                        feats = list(ast.literal_eval(node.value))
                    except Exception:
                        pass
                elif isinstance(tgt, ast.Name) and tgt.id == "TARGET_NAME":
                    try:
                        target = str(ast.literal_eval(node.value))
                    except Exception:
                        pass
    return feats, target


def main() -> int:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    tasks_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_TASKS

    rows = []
    for model_dir in sorted(p for p in out_dir.iterdir() if p.is_dir()):
        for task_dir in sorted(p for p in model_dir.iterdir() if p.is_dir()):
            task = tasks_dir / task_dir.name
            if not task.is_dir():
                continue
            feats, target = verifier_contract(task)
            train = pd.read_csv(next((task / "environment").glob("*.csv")))
            test = pd.read_csv(next((task / "tests").glob("*.csv")))
            var_tr = float(np.var(train[target].to_numpy(float)))
            y = test[target].to_numpy(float)
            var_te = float(np.var(y))
            inputs = test[feats].to_dict(orient="records")

            for trial_dir in sorted(p for p in task_dir.iterdir() if p.is_dir()):
                law_file = trial_dir / "law.py"
                rec = {"model": model_dir.name, "task": task_dir.name,
                       "trial": trial_dir.name}
                rw = trial_dir / "reward.txt"
                rec["official_reward"] = float(rw.read_text().strip()) if rw.exists() else None
                if not law_file.is_file():
                    rec["status"] = "no_law"
                    rows.append(rec)
                    continue
                try:
                    spec = importlib.util.spec_from_file_location(
                        f"law_{model_dir.name}_{trial_dir.name}", law_file)
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    # The 8.28 verifier calls law() with ONE row at a time, in a
                    # randomised order, inside a state-isolated subprocess (see
                    # isolated_predictions in tests/test_outputs.py). Several laws
                    # exploit or assume that and return a single prediction per call,
                    # so a batch call here would wrongly look like a length mismatch.
                    pred = np.asarray([_one(mod.law, row, target) for row in inputs],
                                      dtype=float)
                    if pred.shape != y.shape or not np.all(np.isfinite(pred)):
                        rec["status"] = "bad_predictions"
                        rows.append(rec)
                        continue
                    sse = float(np.mean((pred - y) ** 2))
                    rec["recomputed_r2"] = 1.0 - sse / var_te
                    rec["fixed_scale_r2"] = 1.0 - sse / var_tr
                    rec["rmse"] = float(np.sqrt(sse))
                    rec["status"] = "ok"
                    if rec["official_reward"] is not None:
                        rec["abs_diff_vs_official"] = abs(
                            rec["recomputed_r2"] - rec["official_reward"])
                except Exception as exc:
                    rec["status"] = f"raised: {type(exc).__name__}"
                rows.append(rec)

    cols = ["model", "task", "trial", "status", "official_reward", "recomputed_r2",
            "fixed_scale_r2", "rmse", "abs_diff_vs_official"]
    with (out_dir / "rescore.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    ok = [r for r in rows if r.get("status") == "ok" and r.get("abs_diff_vs_official") is not None]
    # The verifier writes reward.txt with 6 decimals, so agreement is judged at 1e-4.
    mismatch = [r for r in ok if r["abs_diff_vs_official"] > 1e-4
                and r["abs_diff_vs_official"] / max(1.0, abs(r["official_reward"])) > 1e-3]
    summary = {
        "n_laws": len(rows),
        "n_reproduced": len(ok),
        "n_failed_to_run": sum(1 for r in rows if r.get("status", "").startswith("raised")
                               or r.get("status") in ("no_law", "bad_predictions")),
        "n_mismatched_vs_official": len(mismatch),
        "mismatches": [{k: r.get(k) for k in ("model", "task", "official_reward",
                                              "recomputed_r2")} for r in mismatch[:10]],
        "by_model_fixed_scale": {},
    }
    for model in sorted({r["model"] for r in rows}):
        vals = [max(-1.0, min(1.0, float(r["fixed_scale_r2"]))) for r in rows
                if r["model"] == model and r.get("fixed_scale_r2") is not None]
        if vals:
            summary["by_model_fixed_scale"][model] = {
                "n": len(vals),
                "median_clipped_fixed_scale_r2": statistics.median(vals),
                "mean_clipped_fixed_scale_r2": statistics.fmean(vals),
            }
    (out_dir / "rescore_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
