#!/usr/bin/env python3
"""Audit every Bench_test_8.28 task for metric artifacts, before trusting any score.

Two lessons drive this script.  On the earlier SRbench_8_6 sets the holdout was a
right-extrapolation segment whose variance collapsed, so `1 - mse/var(y_test)`
produced rewards like -99999 that said nothing about the model.  On the 8.28
`ai_scaling_u_shape` task the opposite held: the holdout was i.i.d. with train and
noise-free, so a 50-knot spline scored a perfect 1.0 and the metric could not
discriminate at all.  Both failures are invisible if you only read the reward.

For each task this computes, using the task's OWN verifier contract
(FEATURE_NAMES / TARGET_NAME parsed out of tests/test_outputs.py):

  * var(y_test)/var(y_train)      -- < 1e-2 means tiny absolute errors dominate R2
  * the near-zero-variance sentinel's reachability
  * holdout geometry: are test rows inside the train hull, and how far is each
    test row from its nearest train row in std-normalized feature space?
  * a dumb-baseline ladder under the official metric (constant / low-deg
    polynomial / k-NN / RandomForest).  If a dumb baseline already scores ~1.0 the
    task cannot separate models; if even RandomForest scores <0 the holdout is an
    extrapolation regime where R2 is unstable.

Usage: audit_b828_tasks.py [<tasks_dir>] [<out_json>]
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.neighbors import KNeighborsRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures

DEFAULT_TASKS = Path("/data1/SRBench/outputs/harbor_tasks_b828")


def verifier_contract(task: Path) -> tuple[list[str], str]:
    """Parse FEATURE_NAMES / TARGET_NAME out of the task's own verifier."""
    src = (task / "tests" / "test_outputs.py").read_text()
    feats: list[str] = []
    target = ""
    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, ast.Assign):
            continue
        for tgt in node.targets:
            if not isinstance(tgt, ast.Name):
                continue
            if tgt.id == "FEATURE_NAMES":
                try:
                    feats = list(ast.literal_eval(node.value))
                except Exception:
                    pass
            elif tgt.id == "TARGET_NAME":
                try:
                    target = str(ast.literal_eval(node.value))
                except Exception:
                    pass
    return feats, target


def only_csv(directory: Path) -> Path | None:
    files = sorted(directory.glob("*.csv"))
    return files[0] if files else None


def baseline_ladder(Xtr, ytr, Xte, yte) -> dict[str, float]:
    """Test R2 under the official metric for models involving no discovery."""
    var = float(np.var(yte))
    if var < 1e-12:
        return {}

    def r2(pred: np.ndarray) -> float:
        return 1.0 - float(np.mean((pred - yte) ** 2)) / var

    out = {"constant_train_mean": r2(np.full_like(yte, ytr.mean()))}
    n_feat = Xtr.shape[1]
    # Degrees kept modest for multi-feature tasks: PolynomialFeatures blows up
    # combinatorially, and the point is "is this trivially fittable", not "fit it best".
    degrees = (2, 3, 5, 8, 12, 20) if n_feat == 1 else ((2, 3, 4) if n_feat <= 3 else (2, 3))
    for deg in degrees:
        try:
            model = make_pipeline(PolynomialFeatures(deg), LinearRegression())
            model.fit(Xtr, ytr)
            out[f"poly_deg{deg}"] = r2(model.predict(Xte))
        except Exception:
            pass
    for k in (1, 5):
        try:
            knn = KNeighborsRegressor(n_neighbors=k).fit(Xtr, ytr)
            out[f"knn_k{k}"] = r2(knn.predict(Xte))
        except Exception:
            pass
    try:
        rf = RandomForestRegressor(n_estimators=60, random_state=0, n_jobs=1).fit(Xtr, ytr)
        out["random_forest"] = r2(rf.predict(Xte))
    except Exception:
        pass
    return out


def audit(task: Path) -> dict[str, object]:
    rec: dict[str, object] = {"task": task.name}
    feats, target = verifier_contract(task)
    rec["feature_names"], rec["target_name"] = feats, target

    tr_csv, te_csv = only_csv(task / "environment"), only_csv(task / "tests")
    if not (tr_csv and te_csv and feats and target):
        rec["error"] = "could not locate data or verifier contract"
        return rec

    train, test = pd.read_csv(tr_csv), pd.read_csv(te_csv)
    missing = [c for c in (*feats, target) if c not in train.columns or c not in test.columns]
    if missing:
        rec["error"] = f"columns missing from data: {missing}"
        return rec

    Xtr = train[feats].to_numpy(float)
    Xte = test[feats].to_numpy(float)
    ytr = train[target].to_numpy(float)
    yte = test[target].to_numpy(float)

    var_tr, var_te = float(np.var(ytr)), float(np.var(yte))
    rec["n_train"], rec["n_test"] = len(train), len(test)
    rec["var_train"], rec["var_test"] = var_tr, var_te
    rec["var_ratio"] = var_te / var_tr if var_tr > 0 else float("inf")
    # The 8.28 template RAISES on near-zero variance (older sets returned 1e5),
    # which surfaces as reward -1.0 rather than a huge negative number.
    rec["variance_sentinel_reachable"] = bool(var_te < 1e-12)

    # Holdout geometry in std-normalized feature space.
    scale = np.where(Xtr.std(axis=0) > 0, Xtr.std(axis=0), 1.0)
    Ztr, Zte = Xtr / scale, Xte / scale
    # Chunked to keep the pairwise distance matrix bounded in memory.
    nn = np.empty(len(Zte))
    for i in range(0, len(Zte), 256):
        blk = Zte[i:i + 256]
        nn[i:i + 256] = np.sqrt(((blk[:, None, :] - Ztr[None, :, :]) ** 2).sum(-1)).min(axis=1)
    rec["max_nn_dist"] = float(nn.max())
    rec["median_nn_dist"] = float(np.median(nn))

    inside = np.ones(len(Xte), dtype=bool)
    for j in range(Xte.shape[1]):
        inside &= (Xte[:, j] >= Xtr[:, j].min()) & (Xte[:, j] <= Xtr[:, j].max())
    rec["frac_test_inside_train_box"] = float(inside.mean())
    rec["holdout_kind"] = ("interpolation" if rec["max_nn_dist"] < 0.05 and inside.all()
                           else "extrapolation" if inside.mean() < 0.5
                           else "mixed")

    lad = baseline_ladder(Xtr, ytr, Xte, yte)
    rec["baselines"] = lad
    if lad:
        best = max(lad.items(), key=lambda kv: kv[1])
        rec["best_baseline_name"], rec["best_baseline_r2"] = best[0], best[1]

    risks = []
    if rec["variance_sentinel_reachable"]:
        risks.append("zero-variance holdout: verifier raises, reward pinned to -1.0")
    if rec["var_ratio"] < 1e-2:
        risks.append(f"var_test/var_train={rec['var_ratio']:.2e}: tiny absolute errors dominate R2")
    if lad and rec["best_baseline_r2"] > 0.999:
        risks.append(f"saturated: {rec['best_baseline_name']} already scores "
                     f"{rec['best_baseline_r2']:.6f}")
    if lad and rec["best_baseline_r2"] < 0.0:
        risks.append(f"no baseline beats the mean (best {rec['best_baseline_r2']:.3f}): "
                     "genuine extrapolation, R2 unstable")
    rec["risks"] = risks
    rec["artifact_risk"] = "high" if risks else "none"
    return rec


def main() -> int:
    tasks_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TASKS
    out_json = Path(sys.argv[2]) if len(sys.argv) > 2 else \
        Path("/data1/SRBench/harbor_run/b828_task_audit.json")

    results = []
    for task in sorted(p for p in tasks_dir.iterdir() if p.is_dir()):
        try:
            rec = audit(task)
        except Exception as exc:
            rec = {"task": task.name, "error": f"{type(exc).__name__}: {exc}"[:300]}
        results.append(rec)
        flag = rec.get("artifact_risk", "?")
        print(f"{rec['task'][:54]:<54} {rec.get('holdout_kind','?'):<14} "
              f"ratio={rec.get('var_ratio', float('nan')):<11.3e} "
              f"best={rec.get('best_baseline_r2', float('nan')):<12.6f} {flag}")
        for r in rec.get("risks", []):
            print(f"    ! {r}")

    out_json.write_text(json.dumps(results, indent=2) + "\n")
    high = [r["task"] for r in results if r.get("artifact_risk") == "high"]
    print(f"\n{len(results)} tasks audited; {len(high)} flagged high artifact risk")
    print(f"written to {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
