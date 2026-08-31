"""Reject generated targets that contain too little observable variation.

This is a deliberately conservative *data* gate.  It is not a complexity
score and it does not inspect whether an expression looks complicated.  It is
only an ODE trajectory gate: a candidate is rejected when its generated target
has numerically converged to a terminal value during the sampled time window.
Such a task can be solved by outputting the terminal value without recovering
the intended law.

The gate is applied after DataGenSpec generation, before a candidate is
accepted.  It uses the exact generated CSV, so units and parameter scales are
handled relative to the candidate itself.  Reports are JSON-serialisable and
are saved beside the lineage attempt for auditability.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Iterable

import numpy as np


def _read_columns(path: Path, wanted: set[str]) -> tuple[list[str], dict[str, np.ndarray]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {path}")
        missing = wanted - set(reader.fieldnames)
        if missing:
            raise ValueError(f"column(s) {sorted(missing)} are absent from {path}")
        values = {name: [] for name in wanted}
        for row in reader:
            for name in wanted:
                try:
                    values[name].append(float(row[name]))
                except (TypeError, ValueError) as exc:
                    raise ValueError(f"non-numeric value for '{name}' in {path}") from exc
    return list(reader.fieldnames), {name: np.asarray(value, dtype=float) for name, value in values.items()}


def _summary(values: np.ndarray) -> dict[str, float | int | bool]:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return {"n": 0, "finite": False, "std": float("nan"), "range": float("nan")}
    q05, q50, q95 = np.quantile(finite, [0.05, 0.50, 0.95])
    lo, hi = float(np.min(finite)), float(np.max(finite))
    span = hi - lo
    return {
        "n": int(finite.size),
        "finite": True,
        "mean": float(np.mean(finite)),
        "std": float(np.std(finite)),
        "min": lo,
        "max": hi,
        "range": span,
        "robust_range": float(q95 - q05),
        "q05": float(q05),
        "median": float(q50),
        "q95": float(q95),
    }


def _terminal_flatness(
    values: np.ndarray,
    *,
    window_fraction: float,
    flatness_ratio: float,
) -> dict[str, Any]:
    """Detect an ODE trajectory whose visible end has become a flat plateau.

    This intentionally uses one simple visual rule on the ordered, generated
    curve.  Compare the last 20% of points with the immediately preceding
    20%, each relative to the whole-curve range::

        r1 = range(last window) / range(all points)
        r2 = abs(median(last) - median(previous)) / range(all points)

    A candidate is terminally converged only when *both* are below the same
    threshold.  It is a rejection gate for ODE outputs, not a complexity or
    generic low-variation gate for static functions.
    """
    y = np.asarray(values, dtype=float)
    n = len(y)
    if n < 10:
        return {"eligible": False, "reason": "too_few_points"}
    if not np.all(np.isfinite(y)):
        return {"eligible": False, "reason": "nonfinite_values"}

    window = max(1, int(np.floor(window_fraction * n)))
    # The CLI validates window_fraction < 0.5, so both windows are present.
    tail = y[-window:]
    prior = y[-2 * window:-window]
    total_range = float(np.ptp(y))
    terminal_range = float(np.ptp(tail))
    median_shift = float(abs(np.median(tail) - np.median(prior)))
    if total_range == 0.0:
        return {
            "eligible": True,
            "converged": True,
            "reason": "numerically_constant",
            "window_fraction": float(window / n),
            "window_points": window,
            "full_range": total_range,
            "r1_terminal_range_ratio": 0.0,
            "r2_terminal_median_shift_ratio": 0.0,
            "flatness_ratio": flatness_ratio,
        }

    r1 = terminal_range / total_range
    r2 = median_shift / total_range
    return {
        "eligible": True,
        "converged": r1 < flatness_ratio and r2 < flatness_ratio,
        "window_fraction": float(window / n),
        "window_points": window,
        "full_range": total_range,
        "terminal_range": terminal_range,
        "terminal_median_shift": median_shift,
        "r1_terminal_range_ratio": r1,
        "r2_terminal_median_shift_ratio": r2,
        "flatness_ratio": flatness_ratio,
    }


def assess_observable_variation(
    spec: dict[str, Any],
    csv_paths: Iterable[Path],
    *,
    terminal_window_fraction: float = 0.20,
    terminal_flatness_ratio: float = 0.02,
) -> dict[str, Any]:
    """Return an auditable accept/reject report for generated target data.

    The ODE decision is the two-ratio terminal-flatness test over consecutive
    20% windows. Static laws are accepted because a saturated static response
    is not, by itself, numerical time convergence.
    """
    target = str(spec.get("benchmark_output") or spec.get("dependent_variable") or "y")
    paths = [Path(path) for path in csv_paths]
    wanted = {target}
    per_file: list[dict[str, Any]] = []
    all_values: list[np.ndarray] = []
    for path in paths:
        _, columns = _read_columns(path, wanted)
        values = columns[target]
        metrics = _summary(values)
        metrics["csv"] = str(path)
        per_file.append(metrics)
        all_values.append(values)
    if not all_values:
        return {"accepted": False, "decision": "reject_no_data", "target": target}
    combined = np.concatenate(all_values)
    overall = _summary(combined)
    reasons: list[str] = []
    if not overall.get("finite", False) or any(not np.all(np.isfinite(values)) for values in all_values):
        reasons.append("nonfinite_target")
    is_ode = spec.get("integrator") in {"integrate_ode", "integrate_system", "integrate_dde", "integrate_basset"}
    convergence_reports: list[dict[str, Any]] = []
    if is_ode:
        for metrics, values in zip(per_file, all_values):
            convergence = _terminal_flatness(
                values,
                window_fraction=terminal_window_fraction,
                flatness_ratio=terminal_flatness_ratio,
            )
            convergence["csv"] = metrics["csv"]
            convergence_reports.append(convergence)
            if convergence.get("eligible") and convergence.get("converged"):
                reasons.append("numerical_terminal_convergence")

    return {
        "accepted": not reasons,
        "decision": "accept_observable_variation" if not reasons else "reject_low_observable_variation",
        "target": target,
        "integrator": spec.get("integrator"),
        "thresholds": {
            "terminal_window_fraction": terminal_window_fraction,
            "terminal_flatness_ratio": terminal_flatness_ratio,
        },
        "reasons": sorted(set(reasons)),
        "overall": overall,
        "files": per_file,
        "ode_convergence": convergence_reports,
    }
