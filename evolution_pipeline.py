"""Gated equation-evolution pipeline.

Each proposed child is first given a DataGenSpec, then numerically challenged:
can its immediate parent, after refitting its parameters, explain the child's
data in the *unchanged* child sampling domain?  Only children that pass this
test enter the accepted lineage and become parents of later generations.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path

import equation_evolve as evolve
from data_spec_agent_sdk import (
    _attach_ode_benchmark_metadata,
    plan_data_generation,
    validate_sampling_replan,
)
from model_provider import build_model_caller
from parent_refit_gate import evaluate_parent_refit


def _write_jsonl(path: Path, record: dict, mode: str = "a") -> None:
    with path.open(mode, encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def _feedback(report: dict) -> str:
    score = report.get("parent_to_child_r2")
    if isinstance(score, (int, float)):
        return (
            f"The previous proposal was rejected: after fitting the parent parameters, "
            f"the parent achieved holdout R²={score:.6g} on the child data "
            f"(threshold {report.get('threshold_r2'):.6g}). "
            f"Gate mode: {report.get('mode')}. Create a structurally consequential "
            "mechanism, not a weak perturbation or reparameterization."
        )
    return (
        "The previous proposal could not be assessed numerically: "
        f"{report.get('reason', 'unknown reason')}. Keep the same model family and "
        "ensure the proposed mechanism has a well-defined, observable relation."
    )


def _plan_spec(
    record: dict,
    parent: dict | None,
    args: argparse.Namespace,
    *,
    sampling_replan: dict | None = None,
) -> dict:
    spec = plan_data_generation(
        record, args.discipline,
        provider=args.provider,
        base_url=args.base_url,
        auth_source=args.auth_source,
        model=args.spec_model or args.model,
        cli_path=args.cli_path,
        parent=parent,
        sampling_replan=sampling_replan,
        k_sigma=args.k_sigma,
        max_turns=args.spec_max_turns,
    )
    return _attach_ode_benchmark_metadata(spec, record)


def _replan_sampling(
    child: dict,
    parent: dict,
    parent_spec: dict,
    initial_spec: dict,
    initial_report: dict,
    args: argparse.Namespace,
    *,
    fit_seed: int,
    test_seed: int,
) -> tuple[dict, dict]:
    """Give one high-R² child a range-only experimental-design retry."""
    request = {
        "baseline_spec": initial_spec,
        "parent_refit_report": initial_report,
    }
    replanned_spec = _plan_spec(child, parent, args, sampling_replan=request)
    validate_sampling_replan(initial_spec, replanned_spec)
    replanned_report = evaluate_parent_refit(
        parent, child, replanned_spec, parent_spec=parent_spec, reject_r2=args.reject_r2,
        fit_seed=fit_seed,
        test_seed=test_seed,
        n_fit=args.fit_points, n_test=args.test_points,
    )
    return replanned_spec, replanned_report


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evolve one equation with parent-refit gating and one range-only sampling redesign retry.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--input", required=True, help="Stage-3 equations .jsonl/.json")
    parser.add_argument("--id", required=True, help="scenario_id/id of exactly one base equation")
    parser.add_argument("--discipline", default=None, help="defaults to record discipline or science")
    parser.add_argument("--steps", type=int, default=5, help="accepted child generations to produce")
    parser.add_argument("--max-attempts-per-generation", type=int, default=4,
                        help="LLM proposals allowed for one accepted generation")
    parser.add_argument("--p-assumption", type=float, default=0.5)
    parser.add_argument("--assumption-mode", choices=["core", "extended"], default="extended")
    parser.add_argument("--max-static-input-dim", type=int, default=evolve.MAX_STATIC_INPUTS_DEFAULT)
    parser.add_argument("--max-ode-state-dim", type=int, default=evolve.MAX_ODE_STATES_DEFAULT)
    parser.add_argument("--reject-r2", type=float, default=0.90,
                        help="after the one sampling retry, reject if refitted-parent holdout R² remains above this")
    parser.add_argument("--fit-points", type=int, default=1024)
    parser.add_argument("--test-points", type=int, default=1024)
    parser.add_argument("--k-sigma", type=float, default=5.0,
                        help="existing excitation visibility threshold passed to Spec Agent")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--provider", choices=["anthropic", "openrouter"], default="anthropic")
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--auth-source", choices=["auto", "api_key", "auth_token"], default="auto")
    parser.add_argument("--model", default="claude-opus-4-7", help="equation evolution model")
    parser.add_argument("--spec-model", default=None, help="defaults to --model")
    parser.add_argument("--cli-path", default=None, help="Claude CLI path; ignored by OpenRouter Spec Agent")
    parser.add_argument("--spec-max-turns", type=int, default=18)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()

    if not 1 <= args.steps:
        raise SystemExit("--steps must be at least 1")
    if args.max_attempts_per_generation < 1:
        raise SystemExit("--max-attempts-per-generation must be at least 1")
    if not 0.0 <= args.p_assumption <= 1.0:
        raise SystemExit("--p-assumption must be between 0 and 1")
    if not -1.0 <= args.reject_r2 <= 1.0:
        raise SystemExit("--reject-r2 must be in [-1, 1]")

    usable = evolve._load_usable_equations(Path(args.input))
    base = evolve._normalize_base_equation(evolve._select_equation(usable, args.id, False))
    base_id = evolve._eq_id(base)
    args.discipline = args.discipline or base.get("discipline") or "science"
    scenario_text = base.get("scenario_text", "")
    caller = build_model_caller(args.provider, base_url=args.base_url, auth_source=args.auth_source)
    rng = random.Random(args.seed)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    root = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent / "outputs" / "Gated_Evolution"
    out_dir = root / f"gated_{base_id}_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=False)
    lineage_path = out_dir / "accepted_lineage.jsonl"
    specs_path = out_dir / "accepted_specs.jsonl"
    rejected_path = out_dir / "rejected_candidates.jsonl"
    manifest_path = out_dir / "manifest.json"

    manifest = {
        "base_id": base_id, "discipline": args.discipline, "source_input": str(Path(args.input).resolve()),
        "seed": args.seed,
        "sampling_policy": "initial child spec; one range-only replan after an initial high parent-refit R²",
        "gate": {"reject_r2": args.reject_r2, "fit_points": args.fit_points, "test_points": args.test_points},
        "provider": args.provider, "model": args.model, "spec_model": args.spec_model or args.model,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"[gated evolution] {base_id}; accepted generations={args.steps}; "
          f"one sampling replan before rejecting parent R²>{args.reject_r2}", file=sys.stderr)
    print("[gen 0] planning a base spec to retain fixed parent parameter values", file=sys.stderr, flush=True)
    try:
        base_spec = _plan_spec(base, None, args)
    except Exception as exc:
        raise SystemExit(f"Could not plan gen-0 spec: {type(exc).__name__}: {exc}") from exc
    base_record = evolve._record(base, base_id, 0, "base", scenario_text)
    base_record["spec_file"] = specs_path.name
    _write_jsonl(lineage_path, base_record, "w")
    base_spec.update({"record_id": base_id, "generation": 0})
    _write_jsonl(specs_path, base_spec, "w")

    lineage = [base_record]
    current, current_spec = base, base_spec
    for generation in range(1, args.steps + 1):
        feedback: str | None = None
        accepted = False
        for attempt in range(1, args.max_attempts_per_generation + 1):
            child: dict | None = None
            child_spec: dict | None = None
            operation = "change_assumption" if rng.random() < args.p_assumption else "add_term"
            print(f"[gen {generation}, attempt {attempt}] {operation}", file=sys.stderr, flush=True)
            try:
                child = evolve.evolve_once(
                    caller=caller, current=current, operation=operation, discipline=args.discipline,
                    scenario_text=scenario_text, model=args.model, strip_fence=evolve._strip_code_fence,
                    assumption_mode=args.assumption_mode, max_static_inputs=args.max_static_input_dim,
                    max_ode_states=args.max_ode_state_dim, difficulty_feedback=feedback,
                )
                child_spec = _plan_spec(child, current, args)
                fit_seed = args.seed + 10000 * generation + attempt
                test_seed = args.seed + 20000 * generation + attempt
                initial_report = evaluate_parent_refit(
                    current, child, child_spec, parent_spec=current_spec, reject_r2=args.reject_r2,
                    fit_seed=fit_seed, test_seed=test_seed,
                    n_fit=args.fit_points, n_test=args.test_points,
                )
                report = initial_report
                sampling_replan = None
                # A high initial R² has two interpretations: weak/redundant child,
                # or a genuine new effect outside the initial observation window.
                # Give it exactly one range-only design retry before strict evolution.
                if (initial_report.get("status") == "assessed"
                        and initial_report.get("parent_to_child_r2", float("inf")) > args.reject_r2):
                    print("    initial Gate A high R²; attempting one range-only sampling replan...",
                          file=sys.stderr, flush=True)
                    try:
                        replanned_spec, replanned_report = _replan_sampling(
                            child, current, current_spec, child_spec, initial_report, args,
                            fit_seed=fit_seed + 1, test_seed=test_seed + 1,
                        )
                        sampling_replan = {
                            "attempted": True,
                            "initial_spec": child_spec,
                            "initial_gate": initial_report,
                            "replanned_spec": replanned_spec,
                            "replanned_gate": replanned_report,
                        }
                        child_spec, report = replanned_spec, replanned_report
                    except Exception as replan_exc:
                        report = dict(initial_report)
                        report.update({
                            "accepted": False,
                            "decision": "reject_sampling_replan_failed",
                            "reason": "range-only sampling replan failed: "
                                      f"{type(replan_exc).__name__}: {replan_exc}",
                        })
                        sampling_replan = {
                            "attempted": True,
                            "initial_spec": child_spec,
                            "initial_gate": initial_report,
                            "error": report["reason"],
                        }
            except Exception as exc:
                report = {"accepted": False, "decision": "reject_pipeline_error", "mode": "error",
                          "reason": f"{type(exc).__name__}: {exc}", "threshold_r2": args.reject_r2}
                child = child or {"expression": ""}
                initial_report = None
                sampling_replan = None

            audit = {"generation": generation, "attempt": attempt, "operation": operation,
                     "candidate": child, "spec": child_spec, "parent_refit_gate": report,
                     "initial_parent_refit_gate": initial_report,
                     "sampling_replan": sampling_replan}
            if report.get("accepted"):
                rec = evolve._record(child, base_id, generation, operation, scenario_text)
                rec["parent_refit_gate"] = report
                if sampling_replan:
                    rec["sampling_replan"] = sampling_replan
                _write_jsonl(lineage_path, rec)
                child_spec.update({"record_id": base_id, "generation": generation,
                                   "parent_refit_gate": report})
                if sampling_replan:
                    child_spec["sampling_replan"] = sampling_replan
                _write_jsonl(specs_path, child_spec)
                lineage.append(rec)
                current, current_spec = child, child_spec
                print(f"    ACCEPT: parent→child test R²={report.get('parent_to_child_r2'):.6g}", file=sys.stderr)
                accepted = True
                break
            _write_jsonl(rejected_path, audit)
            feedback = _feedback(report)
            print(f"    REJECT after {'sampling replan' if sampling_replan else 'initial Gate A'}: "
                  f"{report.get('reason')}", file=sys.stderr, flush=True)

        if not accepted:
            evolve._build_lineage_xlsx(out_dir / "accepted_lineage.xlsx", lineage)
            raise SystemExit(
                f"Generation {generation} had no accepted child after {args.max_attempts_per_generation} attempts. "
                f"Audit: {rejected_path}"
            )

    evolve._build_lineage_xlsx(out_dir / "accepted_lineage.xlsx", lineage)
    print("\nDone. Only accepted children are in accepted_lineage.jsonl / accepted_specs.jsonl.", file=sys.stderr)
    print(f"Output directory: {out_dir}", file=sys.stderr)
    print("Generate the final accepted benchmark with:", file=sys.stderr)
    print(f"  python data_generator/generate_from_spec.py --spec {specs_path} --index {args.steps} --n-total 5000", file=sys.stderr)


if __name__ == "__main__":
    main()
