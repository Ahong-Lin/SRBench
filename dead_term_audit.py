"""Finalization audit for redundant additive terms.

This module is deliberately conservative.  It can safely prune only a top-level
additive term that is *exactly zero after the final fixed parameters are
substituted*.  A term that merely looks small in the final observation domain is
reported, never automatically deleted: high order is not synonymous with
unnecessary, and a small mechanism may matter under a future experimental design.
"""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import sympy as sp

from data_generator.generate_from_spec import (
    _declared_symbols,
    _lambdify,
    _params,
    _sample_axes,
    gen_integrate_system,
)


ROOT = Path(__file__).resolve().parent


def _metrics(values: np.ndarray, sigma: float) -> dict[str, float | None]:
    values = np.asarray(values, dtype=float)
    absolute = np.abs(values)
    rms = float(np.sqrt(np.mean(absolute ** 2)))
    peak = float(np.max(absolute))
    return {
        "rms": rms,
        "peak": peak,
        "rms_sigma": rms / sigma if sigma > 0 else None,
        "peak_sigma": peak / sigma if sigma > 0 else None,
    }


def _term_rows(
    expression: str,
    arg_names: list[str],
    arg_values: list[np.ndarray],
    params: dict[str, float],
    sigma: float,
    *,
    rms_limit_sigma: float,
    peak_limit_sigma: float,
    mode: str,
) -> tuple[list[dict], str | None]:
    """Evaluate top-level additive terms in one already-fixed design."""
    try:
        _, parsed = _lambdify(expression, arg_names, force_symbols=set(arg_names))
    except Exception as exc:
        return [], f"cannot parse RHS: {type(exc).__name__}: {exc}"
    if not parsed.is_Add:
        return [], None
    substitutions = {sp.Symbol(name): value for name, value in params.items()}
    rows: list[dict] = []
    for index, term in enumerate(parsed.as_ordered_terms()):
        reduced = sp.simplify(term.subs(substitutions))
        row: dict[str, Any] = {
            "term_index": index,
            "term_expression": str(term),
            "after_fixed_parameters": str(reduced),
            "status": "retain",
        }
        if reduced == 0:
            row["status"] = "exact_zero_prunable"
            rows.append(row)
            continue
        try:
            free_names = [name for name in arg_names if name not in params]
            function = sp.lambdify([sp.Symbol(name) for name in free_names], reduced, modules="numpy")
            input_values = [values for name, values in zip(arg_names, arg_values) if name not in params]
            output = np.asarray(function(*input_values), dtype=float)
            output = np.broadcast_to(output, input_values[0].shape if input_values else (1,))
            row.update(_metrics(output, sigma))
            if sigma > 0 and row["rms_sigma"] <= rms_limit_sigma and row["peak_sigma"] <= peak_limit_sigma:
                row["status"] = (
                    "microscopic_static_review" if mode == "static"
                    else "microscopic_trajectory_review"
                )
        except Exception as exc:
            row.update({"status": "excluded_complex_expression",
                        "evaluation_note": f"{type(exc).__name__}: {exc}"})
        rows.append(row)
    return rows, None


def audit_spec(
    spec: dict,
    *,
    n_samples: int = 4096,
    seed: int = 20260803,
    rms_limit_sigma: float = 0.01,
    peak_limit_sigma: float = 0.1,
) -> dict:
    """Audit a final DataGenSpec before dataset generation, without writing data."""
    params = _params(spec)
    sigma = float(spec.get("noise") or 0.0)
    base = {
        "record_id": spec.get("record_id"),
        "generation": spec.get("generation"),
        "equation_type": spec.get("equation_type"),
        "integrator": spec.get("integrator"),
        "rhs_for_integrator": spec.get("rhs_for_integrator"),
        "noise_sigma": sigma,
        "policy": "auto-prune exact zero only; microscopic terms are review-only",
        "rms_limit_sigma": rms_limit_sigma,
        "peak_limit_sigma": peak_limit_sigma,
    }
    if spec.get("equation_type") == "static_explicit" and spec.get("integrator") == "evaluate_explicit":
        axes = spec.get("independent_variables", []) or []
        names = [axis["symbol"] for axis in axes]
        if not names:
            return {**base, "status": "unassessable", "reason": "no independent variables", "terms": []}
        values = _sample_axes(axes, n_samples, seed)
        rows, error = _term_rows(spec["rhs_for_integrator"], names + list(params),
                                 values + [np.full(n_samples, value) for value in params.values()],
                                 params, sigma, rms_limit_sigma=rms_limit_sigma,
                                 peak_limit_sigma=peak_limit_sigma, mode="static")
        return {**base, "status": "assessed" if error is None else "unassessable",
                "mode": "fixed_static_box", "n_samples": n_samples,
                "terms": rows, **({"reason": error} if error else {})}

    if spec.get("integrator") == "integrate_system":
        try:
            columns, data = gen_integrate_system(spec, seed)
            lookup = {name: data[:, index] for index, name in enumerate(columns)}
            time_name = (spec.get("independent_variables") or [{}])[0].get("symbol")
            states = spec.get("state_variables", []) or []
            names = [time_name, *states]
            if not time_name or any(name not in lookup for name in names):
                raise ValueError("trajectory lacks declared time/state columns")
            n = len(data)
            rows, error = _term_rows(spec["rhs_for_integrator"], names + list(params),
                                     [lookup[name] for name in names]
                                     + [np.full(n, value) for value in params.values()],
                                     params, sigma, rms_limit_sigma=rms_limit_sigma,
                                     peak_limit_sigma=peak_limit_sigma, mode="ode")
            return {**base, "status": "assessed" if error is None else "unassessable",
                    "mode": "integrated_child_trajectory", "n_samples": n,
                    "terms": rows, **({"reason": error} if error else {})}
        except Exception as exc:
            return {**base, "status": "unassessable", "mode": "integrated_child_trajectory",
                    "reason": f"could not integrate trajectory: {type(exc).__name__}: {exc}", "terms": []}

    return {**base, "status": "unsupported", "terms": [],
            "reason": "finalization audit currently supports static_explicit and integrate_system"}


def prune_exact_zero_terms(spec: dict, audit: dict | None = None) -> tuple[dict, dict]:
    """Return a copy of a spec with only mathematically exact-zero tails removed."""
    audit = audit or audit_spec(spec)
    prunable = [row for row in audit.get("terms", []) if row.get("status") == "exact_zero_prunable"]
    if not prunable:
        return copy.deepcopy(spec), {"changed": False, "removed_terms": []}
    params = _params(spec)
    arg_names = [item["symbol"] for item in spec.get("independent_variables", []) or []]
    arg_names += list(spec.get("state_variables", []) or []) + list(params)
    _, expression = _lambdify(spec["rhs_for_integrator"], arg_names,
                               force_symbols=_declared_symbols(spec))
    substitutions = {sp.Symbol(name): value for name, value in params.items()}
    retained = [term for term in expression.as_ordered_terms() if sp.simplify(term.subs(substitutions)) != 0]
    replacement = sp.Add(*retained) if retained else sp.Integer(0)
    out = copy.deepcopy(spec)
    out["rhs_for_integrator"] = str(replacement)
    if out.get("integrator") == "integrate_system":
        target = out.get("benchmark_target_state") or out.get("dependent_variable")
        states = out.get("state_variables", []) or []
        if target in states:
            out["state_rhs"][states.index(target)] = str(replacement)
    return out, {"changed": True, "removed_terms": prunable,
                 "old_rhs": spec["rhs_for_integrator"], "new_rhs": str(replacement)}


def _load_specs(path: Path) -> list[dict]:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report exact-zero and microscopic top-level terms in a final DataGenSpec.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--index", type=int, default=-1, help="spec index; -1 is final record")
    parser.add_argument("--samples", type=int, default=4096)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    specs = _load_specs(args.spec)
    spec = specs[args.index]
    report = audit_spec(spec, n_samples=args.samples)
    output = args.output or (ROOT / "outputs" / "quality_reports" /
                             f"dead_term_audit_{datetime.now():%Y%m%d-%H%M%S}.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Wrote audit to {output}")


if __name__ == "__main__":
    main()
