#!/usr/bin/env python3
"""Diagnose the ushape task beyond its official metric.

The official verifier scores ``1 - mse/var(y_test)`` on a holdout that is a 10%
subset of the SAME uniform 5000-point grid as the training data, on noise-free
data.  That metric therefore rewards *interpolation*, and cannot separate a law
that recovered the generating structure from a lookup table.  This script adds
the three checks that do separate them:

  1. **difficulty ladder** -- what test R2 do dumb baselines already get?
  2. **dense-grid recovery** -- error against the analytic ground truth on a grid
     20x finer than train, so it measures the *function*, not the sample.
  3. **extrapolation probe** -- error just outside [-3, 3].  Nothing in the task
     tests this, which is exactly why it exposes memorization.

Usage: diagnose_ushape.py [<outputs_dir>]
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline

TASK = Path("/data1/SRBench/outputs/harbor_tasks_ushape/"
            "SRBench0826_ai_scaling_u_shape_000")


def ground_truth(x: np.ndarray) -> np.ndarray:
    """The task's own reference law (from solution/solve.sh), vectorized.

    Verified to reproduce both CSVs to ~4e-17, i.e. the data is noise-free.
    """
    return (0.02 * x ** 2 + 0.15
            + 0.142337590990431 * (np.tanh((x - 1.5) / 0.5) + 1.0) / 2.0
            - 0.20170751716141724 / (1.0 + np.exp(-(x - 2.0) / 0.5))
            + 0.005 * x ** 3 * (1.0 + 0.5 * np.tanh(x))
            + 0.2 * np.exp(-((x + 1.0) / 0.5) ** 2))


def load_law(path: Path):
    spec = importlib.util.spec_from_file_location(f"law_{path.parent.name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.law


def predict(law, x: np.ndarray) -> np.ndarray:
    rows = [{"logC": float(v)} for v in x]
    out = law(rows)
    return np.asarray([r["Brier"] if isinstance(r, dict) else r for r in out], dtype=float)


def difficulty_ladder(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, float]:
    """Test R2 of baselines that involve no symbolic discovery at all."""
    X, y = train.logC.to_numpy(), train.Brier.to_numpy()
    Xt, yt = test.logC.to_numpy(), test.Brier.to_numpy()
    var = float(np.var(yt))

    def r2(pred: np.ndarray) -> float:
        return 1.0 - float(np.mean((pred - yt) ** 2)) / var

    lad = {"constant (train mean)": r2(np.full_like(yt, y.mean()))}
    for deg in (2, 3, 5, 8, 12, 20):
        lad[f"poly deg {deg}"] = r2(np.polyval(np.polyfit(X, y, deg), Xt))
    srt = train.sort_values("logC")
    sx, sy = srt.logC.to_numpy(), srt.Brier.to_numpy()
    for k in (20, 50, 100):
        idx = np.linspace(0, len(sx) - 1, k).astype(int)
        lad[f"CubicSpline {k} knots"] = r2(CubicSpline(sx[idx], sy[idx])(Xt))
    lad["CubicSpline all 4500 knots"] = r2(CubicSpline(sx, sy)(Xt))
    return lad


def main() -> int:
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1
                   else "/data1/SRBench/harbor_run/ushape_outputs")
    train = pd.read_csv(TASK / "environment" / "train_data.csv")
    test = pd.read_csv(TASK / "tests" / "test_data.csv")

    report: dict[str, object] = {}

    # --- is the data noise-free, and is the holdout in-distribution? ---------
    res_tr = ground_truth(train.logC.to_numpy()) - train.Brier.to_numpy()
    res_te = ground_truth(test.logC.to_numpy()) - test.Brier.to_numpy()
    nn = np.min(np.abs(test.logC.to_numpy()[:, None] - train.logC.to_numpy()[None, :]), axis=1)
    report["data"] = {
        "reference_residual_std_train": float(np.std(res_tr)),
        "reference_residual_std_test": float(np.std(res_te)),
        "noise_free": bool(np.std(res_te) < 1e-12),
        "var_test_over_var_train": float(np.var(test.Brier) / np.var(train.Brier)),
        "max_nearest_train_neighbour_dist": float(nn.max()),
        "grid_spacing_union": float(np.median(np.diff(np.sort(
            np.concatenate([train.logC.to_numpy(), test.logC.to_numpy()]))))),
        "holdout_is_interpolation": bool(nn.max() < 2e-3),
    }
    report["difficulty_ladder"] = difficulty_ladder(train, test)

    # --- per-law recovery + extrapolation -----------------------------------
    segments = {
        "in_range_-3_3": np.linspace(-3, 3, 20001),
        "extrap_left_-4_-3": np.linspace(-4, -3, 5001),
        "extrap_right_3_4": np.linspace(3, 4, 5001),
    }
    laws: list[dict[str, object]] = []
    for model_dir in sorted(p for p in out_dir.iterdir() if p.is_dir()):
        for trial_dir in sorted(p for p in model_dir.iterdir() if p.is_dir()):
            law_file = trial_dir / "law.py"
            if not law_file.is_file():
                continue
            rec: dict[str, object] = {"model": model_dir.name, "trial": trial_dir.name}
            src = law_file.read_text()
            # A law that ships hundreds of constants is a table, not a formula.
            rec["n_numeric_literals"] = sum(c.isdigit() for c in "") or len(
                [t for t in src.replace(",", " ").split() if t.strip("()[],").replace(
                    ".", "").replace("-", "").replace("e", "").isdigit()])
            rec["uses_interpolator"] = any(k in src for k in
                                           ("CubicSpline", "interp1d", "UnivariateSpline"))
            rec["uses_high_deg_poly"] = "polyval" in src or "polyfit" in src
            try:
                law = load_law(law_file)
                for name, grid in segments.items():
                    pred = predict(law, grid)
                    truth = ground_truth(grid)
                    mse = float(np.nanmean((pred - truth) ** 2))
                    rec[f"{name}_rmse"] = float(np.sqrt(mse))
                    rec[f"{name}_r2"] = 1.0 - mse / float(np.var(truth))
            except Exception as exc:
                rec["error"] = str(exc)[:200]
            laws.append(rec)
    report["laws"] = laws

    (out_dir / "diagnosis.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
