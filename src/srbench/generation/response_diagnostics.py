"""Deterministic diagnostics for response-relationship evolution.

These reports do not decide scientific validity and never call a model.  They
make two claims auditable: whether recorded diagnostic coordinates vary in the
published train/hidden design, and whether a parent expression can absorb its
child with one shared parameter set.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd

from srbench.generation.data_generator import _lambdify


def _summary(values: np.ndarray) -> dict[str, Any]:
    values = np.asarray(values, dtype=float).reshape(-1)
    finite = values[np.isfinite(values)]
    if not finite.size:
        return {"n": 0, "finite": False}
    q05, q50, q95 = np.quantile(finite, [0.05, 0.50, 0.95])
    return {
        "n": int(finite.size), "finite": True,
        "min": float(np.min(finite)), "max": float(np.max(finite)),
        "q05": float(q05), "median": float(q50), "q95": float(q95),
        "range": float(np.ptp(finite)), "robust_range": float(q95 - q05),
    }


def _eval_expression(expression: str, frame: pd.DataFrame, parameters: dict[str, float]) -> np.ndarray:
    names = list(frame.columns)
    function, _ = _lambdify(expression, names + list(parameters), force_symbols=set(names) | set(parameters))
    args = [frame[name].to_numpy(dtype=float) for name in names]
    args += [float(parameters[name]) for name in parameters]
    values = np.asarray(function(*args), dtype=float)
    if values.ndim == 0:
        values = np.full(len(frame), float(values))
    return values.reshape(-1)


def _parent_parameter_values(parent: dict, spec: dict, frame: pd.DataFrame) -> tuple[list[str], dict[str, float]]:
    spec_values = {str(item["symbol"]): float(item["value"])
                   for item in spec.get("parameters", [])}
    symbols = [symbol for symbol, role in zip(parent.get("symbols", []), parent.get("symbol_properties", []))
               if role == "P" and symbol not in frame.columns]
    return symbols, {symbol: spec_values.get(symbol, 1.0) for symbol in symbols}


def _status(summary: dict[str, Any]) -> str:
    if not summary.get("finite") or summary.get("n", 0) < 2:
        return "inactive"
    scale = max(1.0, abs(float(summary.get("median", 0.0))))
    return "visible" if float(summary.get("robust_range", 0.0)) > 1e-3 * scale else "inactive"


def mechanism_coverage(spec: dict, train: pd.DataFrame, hidden: pd.DataFrame) -> dict[str, Any]:
    """Evaluate all recorded diagnostic groups on two public partitions."""
    parameters = {str(item["symbol"]): float(item["value"])
                  for item in spec.get("parameters", [])}
    history = spec.get("mechanism_observation_history") or []
    groups: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for item in history:
        contract = item.get("contract") or {}
        for group in contract.get("diagnostic_groups") or []:
            name, expression = str(group.get("name", "")), str(group.get("expression", ""))
            key = (name, expression)
            if name and expression and key not in seen:
                seen.add(key)
                groups.append({"generation": item.get("generation"), **group})
    report: list[dict[str, Any]] = []
    for group in groups:
        row = dict(group)
        try:
            train_values = _eval_expression(group["expression"], train.drop(columns=[c for c in ("partition",) if c in train]), parameters)
            hidden_values = _eval_expression(group["expression"], hidden.drop(columns=[c for c in ("partition",) if c in hidden]), parameters)
            train_summary = _summary(train_values)
            hidden_summary = _summary(hidden_values)
            train_status = _status(train_summary)
            if train_status == "inactive":
                hidden_status = "inactive"
            else:
                outside = (hidden_summary.get("q05", math.inf) < train_summary.get("q05", -math.inf) - 1e-12 or
                            hidden_summary.get("q95", -math.inf) > train_summary.get("q95", math.inf) + 1e-12)
                hidden_status = "extended" if outside else "visible"
            row.update({"train_range": [train_summary.get("min"), train_summary.get("max")],
                        "hidden_range": [hidden_summary.get("min"), hidden_summary.get("max")],
                        "train_status": train_status, "hidden_status": hidden_status,
                        "crosses_boundary": hidden_status == "extended",
                        "train_summary": train_summary, "hidden_summary": hidden_summary})
        except Exception as exc:
            row.update({"train_status": "inactive", "hidden_status": "inactive",
                        "crosses_boundary": False, "error": f"{type(exc).__name__}: {exc}"})
        report.append(row)
    return {
        "groups": report,
        "inactive_mechanisms": [r["name"] for r in report if r.get("train_status") == "inactive"],
        "visible_mechanisms": [r["name"] for r in report if r.get("train_status") == "visible"],
        "extended_mechanisms": [r["name"] for r in report if r.get("hidden_status") == "extended"],
    }


def _parent_frame(frame: pd.DataFrame, parent: dict, child_spec: dict) -> pd.DataFrame:
    """Use fixed reference values for parent parameters promoted to inputs."""
    out = frame.copy()
    child_params = {str(item["symbol"]): float(item["value"])
                    for item in child_spec.get("parameters", [])}
    for symbol, role in zip(parent.get("symbols", []), parent.get("symbol_properties", [])):
        if role == "P" and symbol not in out:
            out[symbol] = child_params.get(symbol, 1.0)
    return out


def parent_absorption(parent: dict | None, child: dict, spec: dict, train: pd.DataFrame, hidden: pd.DataFrame,
                      *, max_points: int = 2000) -> dict[str, Any]:
    """Report fixed-parent and least-squares refit errors against the child law."""
    if not parent or not parent.get("expression"):
        return {"status": "unavailable", "reason": "no_parent_record"}
    frame = pd.concat([train, hidden], ignore_index=True)
    if len(frame) > max_points:
        frame = frame.iloc[np.linspace(0, len(frame) - 1, max_points).astype(int)]
    params = {str(item["symbol"]): float(item["value"])
              for item in spec.get("parameters", [])}
    try:
        child_values = _eval_expression(child["expression"], frame, params)
        parent_frame = _parent_frame(frame, parent, spec)
        fit_symbols, parent_params = _parent_parameter_values(parent, spec, parent_frame)
        parent_values = _eval_expression(parent["expression"], parent_frame, parent_params)
        scale = max(float(np.median(np.abs(child_values - np.median(child_values)))), 1e-12)
        fixed_rmse = float(np.sqrt(np.mean((parent_values - child_values) ** 2)) / scale)
        refit = {"status": "not_run", "reason": "no free parent parameters"}
        if fit_symbols:
            from scipy.optimize import least_squares
            x0 = np.asarray([parent_params[name] for name in fit_symbols], dtype=float)
            bound = 100.0 * np.maximum(1.0, np.abs(x0)) + 10.0

            def residual(theta):
                values = _eval_expression(parent["expression"], parent_frame,
                                           dict(zip(fit_symbols, map(float, theta))))
                values = np.where(np.isfinite(values), values, 1e100)
                return np.clip(values - child_values, -1e100, 1e100)

            result = least_squares(residual, x0, bounds=(x0 - bound, x0 + bound), max_nfev=120)
            fitted = residual(result.x)
            refit = {
                "status": "ok", "parameters": {name: float(value) for name, value in zip(fit_symbols, result.x)},
                "normalized_rmse": float(np.sqrt(np.mean(fitted ** 2)) / scale),
                "optimizer_success": bool(result.success),
            }
        return {"status": "ok", "n_points": int(len(frame)), "fixed_parent_normalized_rmse": fixed_rmse,
                "refit": refit,
                "interpretation": "<1e-3 nearly absorbed; 1e-3..1e-2 weak; >1e-2 visible structure"}
    except Exception as exc:
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}
