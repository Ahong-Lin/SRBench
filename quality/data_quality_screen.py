"""Stage 6c (report-only): audit generated benchmark data for weak evidence.

This script does not change equations, specs, or CSV files.  It joins generated
CSV files to their exact DataGenSpec records and writes diagnostics that help
decide which future acceptance rules are justified by the actual corpus.

The diagnostics deliberately distinguish two units:
  * syntactic RHS terms, which are useful for finding tiny/local numerical parts;
  * child-minus-parent differences, which are the meaningful unit for an evolved
    scientific mechanism.  A mechanism can span several algebraic terms.

It is a screening report, not a proof of practical identifiability: it does not
refit a reduced model.  That likelihood-ratio step can be added after examining
the corpus-level distributions produced here.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import sympy as sp


# This module lives under ``quality/``; repository-relative default paths still
# belong at the project root.
ROOT = Path(__file__).resolve().parent.parent
CSV_NAME_RE = re.compile(r"^(.*)_gen(\d+)_\d{8}-\d{6}\.csv$")
IDENTIFIER_RE = re.compile(r"^[A-Za-z_]\w*$")
MATH_NAMES = {
    "Abs", "Max", "Min", "Piecewise", "Heaviside",
    "sin", "cos", "tan", "asin", "acos", "atan",
    "sinh", "cosh", "tanh", "exp", "log", "sqrt",
    "sign", "floor", "ceiling", "pi", "E", "I", "oo", "nan", "True", "False",
}


def _json_lines(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at {path}:{line_no}: {exc}") from exc
        if isinstance(value, dict):
            records.append(value)
    return records


def _spec_fingerprint(spec: dict[str, Any]) -> str:
    keys = [
        "record_id", "generation", "equation_type", "integrator",
        "dependent_variable", "benchmark_output", "benchmark_target_state",
        "independent_variables", "parameters", "rhs_for_integrator",
        "state_variables", "state_rhs", "initial_conditions", "noise",
    ]
    return json.dumps({key: spec.get(key) for key in keys}, sort_keys=True)


def _expected_columns(spec: dict[str, Any]) -> list[str]:
    independent = [str(item["symbol"]) for item in spec.get("independent_variables", [])]
    if spec.get("integrator") == "integrate_system":
        columns = independent + [str(item) for item in spec.get("state_variables", [])]
        output = spec.get("benchmark_output")
        target_state = spec.get("benchmark_target_state")
        if output and target_state in spec.get("state_variables", []):
            columns.append(str(output))
            if float(spec.get("noise") or 0.0) > 0:
                columns.append(f"{output}_noisy")
            return columns
        dependent = str(spec.get("dependent_variable", "y"))
        if float(spec.get("noise") or 0.0) > 0 and dependent in spec.get("state_variables", []):
            columns.append(f"{dependent}_noisy")
        return columns

    dependent = str(spec.get("dependent_variable", "y"))
    return independent + [dependent] + (
        [f"{dependent}_noisy"] if float(spec.get("noise") or 0.0) > 0 else []
    )


def _load_spec_catalog(spec_paths: list[Path]) -> list[tuple[str, dict[str, Any]]]:
    unique: dict[str, tuple[str, dict[str, Any]]] = {}
    for path in spec_paths:
        for record in _json_lines(path):
            if "rhs_for_integrator" not in record:
                continue
            unique.setdefault(_spec_fingerprint(record), (path.name, record))
    return list(unique.values())


def _csv_columns(path: Path) -> list[str]:
    with path.open(encoding="utf-8") as handle:
        return handle.readline().strip().split(",")


def _match_spec(
    csv_path: Path,
    catalog: list[tuple[str, dict[str, Any]]],
) -> tuple[str, dict[str, Any]]:
    match = CSV_NAME_RE.match(csv_path.name)
    if not match:
        raise ValueError("CSV name does not contain '<record>_gen<N>_<timestamp>'")
    record_id, generation = match.group(1), int(match.group(2))
    columns = _csv_columns(csv_path)
    matches = [
        (source, spec)
        for source, spec in catalog
        if spec.get("record_id") == record_id
        and spec.get("generation") == generation
        and _expected_columns(spec) == columns
    ]
    if len(matches) != 1:
        raise ValueError(f"matched {len(matches)} candidate specs")
    return matches[0]


def _symbols_for(spec: dict[str, Any], columns: dict[str, np.ndarray], expression: str) -> dict[str, Any]:
    declared = set(columns)
    declared |= {str(item["symbol"]) for item in spec.get("parameters", [])}
    declared |= {str(item["symbol"]) for item in spec.get("independent_variables", [])}
    declared |= {str(item) for item in spec.get("state_variables", [])}
    expression_names = set(re.findall(r"\b[A-Za-z_]\w*\b", expression))
    # Declared names take precedence, so a legitimate current `I` remains a
    # variable, while standard callable names such as exp/sqrt stay callable.
    names = declared | {name for name in expression_names if name not in MATH_NAMES}
    return {name: sp.Symbol(name) for name in names if IDENTIFIER_RE.match(name)}


def _parse_expression(
    expression: str,
    spec: dict[str, Any],
    columns: dict[str, np.ndarray],
) -> tuple[sp.Expr, list[str], list[np.ndarray]]:
    local = _symbols_for(spec, columns, expression)
    parsed = sp.sympify(expression, locals=local)
    substitutions = {
        sp.Symbol(str(item["symbol"])): float(item["value"])
        for item in spec.get("parameters", [])
    }
    parsed = parsed.subs(substitutions)
    free = sorted(str(symbol) for symbol in parsed.free_symbols)
    missing = [name for name in free if name not in columns]
    if missing:
        raise ValueError("expression needs unavailable data columns: " + ", ".join(missing))
    arguments = [local.get(name, sp.Symbol(name)) for name in free]
    values = [columns[name] for name in free]
    return parsed, free, values


def _evaluate(expression: sp.Expr, free: list[str], values: list[np.ndarray]) -> np.ndarray:
    arguments = [sp.Symbol(name) for name in free]
    function = sp.lambdify(arguments, expression, modules="numpy")
    shape = np.broadcast(*values).shape if values else (1,)
    try:
        result = np.asarray(function(*values), dtype=float)
        return np.broadcast_to(result, shape).astype(float)
    except (TypeError, ValueError):
        # SymPy's NumPy printer represents nested Max/Min with np.asarray([...]).
        # A scalar and an array then cannot always be packed together, although the
        # same expression is well-defined point by point.  Fall back only for such
        # expressions so the diagnostic does not mistake a vectorization limitation
        # for a bad benchmark instance.
        if not values:
            raise
        broadcast_values = np.broadcast_arrays(*values)
        flat_values = [value.ravel() for value in broadcast_values]
        scalar_values = np.fromiter(
            (float(function(*point)) for point in zip(*flat_values)),
            dtype=float,
            count=flat_values[0].size,
        )
        return scalar_values.reshape(shape)


def _sigma_metrics(values: np.ndarray, sigma: float) -> dict[str, float | None]:
    abs_values = np.abs(values)
    rms = float(np.sqrt(np.mean(values ** 2)))
    if sigma <= 0:
        return {
            "rms": rms,
            "rms_sigma": None,
            "active_fraction_1sigma": None,
            "active_fraction_5sigma": None,
            "near_zero_fraction_1sigma": None,
            "peak_to_rms": float(np.max(abs_values) / max(rms, 1e-300)),
        }
    return {
        "rms": rms,
        "rms_sigma": rms / sigma,
        "active_fraction_1sigma": float(np.mean(abs_values >= sigma)),
        "active_fraction_5sigma": float(np.mean(abs_values >= 5.0 * sigma)),
        "near_zero_fraction_1sigma": float(np.mean(abs_values < sigma)),
        "peak_to_rms": float(np.max(abs_values) / max(rms, 1e-300)),
    }


def _active_region(
    active: np.ndarray,
    axes: list[str],
    columns: dict[str, np.ndarray],
) -> str:
    if not axes or not np.any(active):
        return "{}"
    summary = {
        name: [float(np.quantile(columns[name][active], 0.05)),
               float(np.quantile(columns[name][active], 0.95))]
        for name in axes
        if name in columns
    }
    return json.dumps(summary, ensure_ascii=False)


def _lineage_parent(
    spec: dict[str, Any],
    lineage_dir: Path,
    source_spec: str,
) -> tuple[dict[str, Any] | None, str]:
    """Find the immediate parent, including older specs without source_lineage."""
    source = str(spec.get("source_lineage") or "")
    link_source = "source_lineage"
    if not source:
        # Older per-lineage specs lack source_lineage, but their file names retain
        # an exact link: evolution_<id>_<run>_last_spec.jsonl.
        stem = Path(source_spec).stem
        suffix = "_last_spec"
        if stem.startswith("evolution_") and stem.endswith(suffix):
            source = stem[:-len(suffix)]
            link_source = "source_spec_filename"
    generation = spec.get("generation")
    if not source or not isinstance(generation, int) or generation <= 0:
        return None, "none"
    path = lineage_dir / f"{source}.jsonl"
    if not path.exists():
        return None, "missing_lineage_file"
    records = _json_lines(path)
    for index, record in enumerate(records):
        if record.get("generation") == generation:
            return (records[index - 1] if index else None), link_source
    return None, "generation_not_found"


def _parent_delta(
    spec: dict[str, Any],
    parent: dict[str, Any] | None,
    columns: dict[str, np.ndarray],
    child_values: np.ndarray,
    sigma: float,
) -> tuple[dict[str, Any], str | None]:
    if parent is None or not parent.get("expression"):
        return {}, None
    try:
        parent_expr, free, values = _parse_expression(str(parent["expression"]), spec, columns)
        parent_values = _evaluate(parent_expr, free, values)
        delta = child_values - parent_values
        metrics = _sigma_metrics(delta, sigma)
        axes = [str(item["symbol"]) for item in spec.get("independent_variables", [])]
        metrics["active_region_5sigma"] = _active_region(
            np.abs(delta) >= 5.0 * sigma if sigma > 0 else np.ones(delta.shape, dtype=bool),
            axes,
            columns,
        )
        return metrics, None
    except Exception as exc:
        return {}, f"{type(exc).__name__}: {exc}"


def _term_rows(
    parsed: sp.Expr,
    free: list[str],
    values: list[np.ndarray],
    spec: dict[str, Any],
    csv_name: str,
    sigma: float,
    axes: list[str],
    columns: dict[str, np.ndarray],
) -> list[dict[str, Any]]:
    terms = parsed.as_ordered_terms() if parsed.is_Add else [parsed]
    rows: list[dict[str, Any]] = []
    for index, term in enumerate(terms):
        term_values = _evaluate(term, free, values)
        metrics = _sigma_metrics(term_values, sigma)
        active = np.abs(term_values) >= 5.0 * sigma if sigma > 0 else np.ones(term_values.shape, dtype=bool)
        flags: list[str] = []
        if metrics["rms_sigma"] is not None and float(metrics["rms_sigma"]) < 5.0:
            flags.append("rms_below_5sigma")
        if metrics["active_fraction_5sigma"] is not None and float(metrics["active_fraction_5sigma"]) < 0.05:
            flags.append("active_below_5pct")
        rows.append({
            "csv_file": csv_name,
            "record_id": spec.get("record_id"),
            "generation": spec.get("generation"),
            "term_index": index,
            "term_expression": str(term),
            **metrics,
            "active_region_5sigma": _active_region(active, axes, columns),
            "attention_flags": ";".join(flags),
        })
    return rows


def _variable_rows(
    parsed: sp.Expr,
    free: list[str],
    values: list[np.ndarray],
    child_values: np.ndarray,
    spec: dict[str, Any],
    csv_name: str,
    sigma: float,
) -> list[dict[str, Any]]:
    if spec.get("equation_type") != "explicit":
        return []
    rng = np.random.default_rng(20260803)
    rows: list[dict[str, Any]] = []
    for item in spec.get("independent_variables", []):
        name = str(item["symbol"])
        if name not in free:
            continue
        permuted = [value.copy() for value in values]
        permuted[free.index(name)] = rng.permutation(permuted[free.index(name)])
        alternate = _evaluate(parsed, free, permuted)
        alternate = np.broadcast_to(alternate, child_values.shape)
        effect = float(np.sqrt(np.mean((alternate - child_values) ** 2)))
        effect_sigma = effect / sigma if sigma > 0 else None
        flags = []
        if effect_sigma is not None and effect_sigma < 5.0:
            flags.append("permutation_effect_below_5sigma")
        rows.append({
            "csv_file": csv_name,
            "record_id": spec.get("record_id"),
            "generation": spec.get("generation"),
            "variable": name,
            "permutation_rms_effect": effect,
            "permutation_rms_sigma": effect_sigma,
            "attention_flags": ";".join(flags),
        })
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _screen_one(
    csv_path: Path,
    source_spec: str,
    spec: dict[str, Any],
    lineage_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    data = np.genfromtxt(csv_path, delimiter=",", names=True, dtype=float, encoding="utf-8")
    if data.dtype.names is None:
        raise ValueError("CSV has no header")
    columns = {name: np.asarray(data[name], dtype=float) for name in data.dtype.names}
    output = str(spec.get("benchmark_output") or spec.get("dependent_variable") or "y")
    sigma = float(spec.get("noise") or 0.0)
    if output not in columns:
        raise ValueError(f"benchmark output '{output}' is not in CSV")
    child_values = columns[output]
    noisy = columns.get(f"{output}_noisy")
    axes = [str(item["symbol"]) for item in spec.get("independent_variables", [])]
    summary: dict[str, Any] = {
        "csv_file": csv_path.name,
        "source_spec": source_spec,
        "record_id": spec.get("record_id"),
        "generation": spec.get("generation"),
        "equation_type": spec.get("equation_type"),
        "integrator": spec.get("integrator"),
        "n_points": int(len(data)),
        "input_dimension": len(axes),
        "state_count": len(spec.get("state_variables", [])),
        "benchmark_output": output,
        "noise_sigma": sigma,
        "output_std": float(np.std(child_values)),
        "output_range": float(np.max(child_values) - np.min(child_values)),
        "output_std_over_sigma": float(np.std(child_values) / sigma) if sigma > 0 else None,
        "empirical_noise_std": float(np.std(noisy - child_values)) if noisy is not None else None,
        "source_lineage": spec.get("source_lineage", ""),
    }
    parsed, free, values = _parse_expression(str(spec["rhs_for_integrator"]), spec, columns)
    evaluated = _evaluate(parsed, free, values)
    summary["rhs_csv_rmse"] = float(np.sqrt(np.mean((evaluated - child_values) ** 2)))
    terms = _term_rows(parsed, free, values, spec, csv_path.name, sigma, axes, columns)
    variables = _variable_rows(parsed, free, values, evaluated, spec, csv_path.name, sigma)
    parent_record, parent_link = _lineage_parent(spec, lineage_dir, source_spec)
    summary["parent_link"] = parent_link
    parent, parent_error = _parent_delta(
        spec, parent_record, columns, evaluated, sigma,
    )
    summary.update({f"parent_rhs_delta_on_child_data_{key}": value for key, value in parent.items()})
    if parent_error:
        summary["parent_delta_error"] = parent_error

    flags: list[str] = []
    if sigma > 0 and summary["output_std_over_sigma"] < 5.0:
        flags.append("low_global_snr")
    if any(term["attention_flags"] for term in terms):
        flags.append("weak_or_local_syntactic_term")
    if any(variable["attention_flags"] for variable in variables):
        flags.append("low_effect_static_input")
    # For static equations this compares the exact parent and child mappings on
    # the observed samples.  For ODEs it is only a local RHS diagnostic; a proper
    # parent-child system comparison requires re-integrating both systems.
    if spec.get("equation_type") == "explicit" and parent and parent.get("rms_sigma") is not None:
        if float(parent["rms_sigma"]) < 5.0:
            flags.append("weak_child_parent_difference")
        if float(parent["active_fraction_5sigma"]) < 0.05:
            flags.append("local_child_parent_difference")
    summary["attention_flags"] = ";".join(flags)
    summary["attention_flag_count"] = len(flags)
    return summary, terms, variables


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stage 6c report-only screen for generated symbolic-regression data.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--spec", type=Path,
        default=ROOT / "outputs" / "data_5000" / "specs_resume_after_skip.jsonl",
        help="JSONL containing the specs used to generate the CSV files",
    )
    parser.add_argument(
        "--data-dir", type=Path, default=ROOT / "outputs" / "data_5000",
        help="directory containing generated CSV files",
    )
    parser.add_argument(
        "--lineage-dir", type=Path, default=ROOT / "logs" / "Evolved_Equations",
        help="directory holding evolution_*.jsonl files for parent comparisons",
    )
    parser.add_argument(
        "--spec-dir", type=Path, action="append",
        default=[ROOT / "logs" / "Specs"],
        help="directory of additional per-lineage DataGenSpec JSONL files; repeatable",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="directory for reports; default creates outputs/quality_reports/<timestamp>",
    )
    args = parser.parse_args()

    if not args.spec.exists():
        raise SystemExit(f"spec file not found: {args.spec}")
    if not args.data_dir.exists():
        raise SystemExit(f"data directory not found: {args.data_dir}")

    spec_paths = [args.spec]
    for spec_dir in args.spec_dir:
        if not spec_dir.exists():
            print(f"warning: spec directory not found: {spec_dir}", file=sys.stderr)
            continue
        spec_paths.extend(sorted(spec_dir.glob("*.jsonl")))
    catalog = _load_spec_catalog(spec_paths)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = args.output_dir or (ROOT / "outputs" / "quality_reports" / timestamp)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_rows: list[dict[str, Any]] = []
    term_rows: list[dict[str, Any]] = []
    variable_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for csv_path in sorted(args.data_dir.glob("*.csv")):
        try:
            source_spec, spec = _match_spec(csv_path, catalog)
            summary, terms, variables = _screen_one(
                csv_path, source_spec, spec, args.lineage_dir,
            )
            summary_rows.append(summary)
            term_rows.extend(terms)
            variable_rows.extend(variables)
        except Exception as exc:
            failures.append({
                "csv_file": csv_path.name,
                "error": f"{type(exc).__name__}: {exc}",
            })

    _write_csv(output_dir / "dataset_summary.csv", summary_rows)
    _write_csv(output_dir / "term_diagnostics.csv", term_rows)
    _write_csv(output_dir / "variable_diagnostics.csv", variable_rows)
    _write_csv(output_dir / "screen_failures.csv", failures)
    with (output_dir / "dataset_summary.jsonl").open("w", encoding="utf-8") as handle:
        for row in summary_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    overview = {
        "stage": "6c report-only quality screen",
        "created": timestamp,
        "spec": str(args.spec),
        "data_dir": str(args.data_dir),
        "lineage_dir": str(args.lineage_dir),
        "datasets_screened": len(summary_rows),
        "screen_failures": len(failures),
        "equation_types": dict(Counter(row["equation_type"] for row in summary_rows)),
        "datasets_with_attention": sum(bool(row["attention_flags"]) for row in summary_rows),
        "term_units": len(term_rows),
        "term_units_with_attention": sum(bool(row["attention_flags"]) for row in term_rows),
        "static_inputs": len(variable_rows),
        "static_inputs_with_attention": sum(bool(row["attention_flags"]) for row in variable_rows),
        "note": (
            "Attention flags are descriptive defaults (5 sigma and 5 percent active "
            "coverage), not benchmark rejection rules. No equation or data file was modified."
        ),
    }
    (output_dir / "overview.json").write_text(
        json.dumps(overview, ensure_ascii=False, indent=2) + "\n", encoding="utf-8",
    )

    print(json.dumps(overview, ensure_ascii=False, indent=2))
    print(f"Wrote report to {output_dir}", file=sys.stderr)


if __name__ == "__main__":
    main()
