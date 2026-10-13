"""Generate one mechanism-guided lineage and its candidate data.

Harbor packaging and solver scoring belong to separate stages in v7.
"""
from __future__ import annotations
import argparse
import json
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
import numpy as np
from srbench.generation import evolution as evolve
from srbench.generation.data_generator import CandidateDataError, generate
from srbench.generation.data_spec import _attach_ode_benchmark_metadata, plan_data_generation
from srbench.generation.observable import assess_observable_variation
from srbench.common.contracts import noiseless_spec
from srbench.common.model_provider import ModelServiceError, build_model_caller
from srbench.common.io import write_json as _write_json, append_jsonl as _write_jsonl, read_json, read_jsonl
from srbench.generation.checkpoints import latest_run, attempt_outcomes, candidate_failure

def _plan_spec(record: dict, parent: dict | None, args: argparse.Namespace, *, replan: dict | None = None) -> dict:
    record = dict(record)
    spec = plan_data_generation(
        record, args.discipline, provider=args.provider, base_url=args.base_url,
        auth_source=args.auth_source, model=args.spec_model or args.model,
        cli_path=args.cli_path, parent=parent, sampling_replan=replan,
        max_turns=args.spec_max_turns,
    )
    return _attach_ode_benchmark_metadata(noiseless_spec(spec), record)


def _generate(spec: dict, base_id: str, generation: int, output_dir: Path,
              seed: int, n_total: int, partition: str | None = None) -> tuple[dict, Path]:
    local = noiseless_spec(spec)
    local.update({"record_id": base_id, "generation": generation, "_n_total": n_total})
    if partition is not None:
        local["_partition"] = partition
    try:
        result = generate(local, output_dir, seed=seed, verbose=False)
    except (FloatingPointError, ZeroDivisionError, OverflowError) as exc:
        raise CandidateDataError(f"numeric evaluation failed: {type(exc).__name__}: {exc}") from exc
    return local, Path(result["csv_path"])


def _observable_gate(
    spec: dict,
    csv_paths: list[Path],
    args: argparse.Namespace,
) -> dict[str, Any]:
    """Screen generated target variation before expensive Harbor/solver work."""
    return assess_observable_variation(
        spec,
        csv_paths,
        terminal_window_fraction=args.observable_terminal_window_fraction,
        terminal_flatness_ratio=args.observable_terminal_flatness_ratio,
    )


def _response_reports(spec: dict, final: dict, parent: dict | None, args: argparse.Namespace) -> dict:
    """Run local train/hidden response audits without another model call."""
    try:
        from srbench.common.contracts import contract_from_spec
        from srbench.packaging.split import build_split
        from srbench.generation.response_diagnostics import mechanism_coverage, parent_absorption

        contract = contract_from_spec(noiseless_spec(spec))
        audit_total = min(512, max(64, int(args.n_total)))
        audit_hidden = max(16, min(128, audit_total // 4))
        train, hidden, _ = build_split(
            noiseless_spec(spec), contract, n_total=audit_total,
            test_points=audit_hidden, seed=int(args.seed) + 100003,
        )
        coverage = mechanism_coverage(spec, train, hidden)
        target = contract.target
        target_variance = {
            "train": {"n": int(len(train)), "variance": float(train[target].var(ddof=0)),
                      "range": float(train[target].max() - train[target].min())},
            "hidden": {"n": int(len(hidden)), "variance": float(hidden[target].var(ddof=0)),
                       "range": float(hidden[target].max() - hidden[target].min())},
        }
        absorption = parent_absorption(parent, final, spec, train, hidden)
        return {"coverage_report": coverage, "inactive_mechanisms": coverage.get("inactive_mechanisms", []),
                "target_variance": target_variance, "parent_absorption_report": absorption}
    except Exception as exc:
        return {"coverage_report": {"status": "error", "error": f"{type(exc).__name__}: {exc}"},
                "inactive_mechanisms": [], "target_variance": {},
                "parent_absorption_report": {"status": "error", "error": f"{type(exc).__name__}: {exc}"}}


def _write_lineage(path: Path, lineage: list[dict]) -> None:
    temporary = path.with_suffix(".tmp")
    temporary.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in lineage), encoding="utf-8")
    temporary.replace(path)


def _tuple_state(value):
    return tuple(_tuple_state(item) for item in value) if isinstance(value, list) else value


def _restore_rng(rng, directory, lineage, args):
    """Replay legacy selection draws, or restore the saved post-selection state."""
    for generation in range(1, len(lineage) + 1):
        path = directory / f"gen_{generation:03d}_selection.json"
        if not path.exists():
            break
        selection = read_json(path)
        if "rng_state_after" in selection:
            rng.setstate(_tuple_state(selection["rng_state_after"]))
        else:
            if args.operation_policy == "random":
                rng.random()
            evolve.sample_embedding_pattern(
                rng, lineage[generation - 1], selection["operation"], args.assumption_mode,
                evolution_plan=selection.get("plan"),
            )


def _resume_lineage(base_record, directory, args):
    lineage = read_jsonl(directory / "lineage.jsonl")
    if not lineage:
        return [base_record]
    for key in ("base_id", "expression", "target_symbol", "model_family", "equation_type",
                "symbols", "symbol_properties", "ode_system"):
        if lineage[0].get(key) != base_record.get(key):
            raise ValueError(f"Checkpoint baseline differs at {key}: {directory}")
    if [row.get("generation") for row in lineage] != list(range(len(lineage))):
        raise ValueError(f"Checkpoint generations are not contiguous: {directory}")
    if len(lineage) - 1 > args.max_steps:
        raise ValueError("Checkpoint exceeds the configured generation budget")
    return lineage


def _lineage(base: dict, base_id: str, caller: Any, args: argparse.Namespace,
             rng: random.Random, feedback: str | None,
             checkpoint_dir: Path | None = None) -> tuple[list[dict], dict]:
    scenario = base.get("scenario_text", "")
    lineage = [evolve._record(base, base_id, 0, "base", scenario)]
    if checkpoint_dir is not None and getattr(args, "resume", False):
        lineage = _resume_lineage(lineage[0], checkpoint_dir, args)
        _restore_rng(rng, checkpoint_dir, lineage, args)
        print(f"[resume] {len(lineage) - 1} completed generations; {checkpoint_dir}", file=sys.stderr, flush=True)
    current = lineage[-1] if len(lineage) > 1 else base

    def save_progress(stage: str, generation: int) -> None:
        if checkpoint_dir is not None:
            checkpoint_dir.mkdir(parents=True, exist_ok=True)
            # Persist the actual lineage before publishing its progress counter.
            _write_lineage(checkpoint_dir / "lineage.jsonl", lineage)
            _write_json(checkpoint_dir / "progress.json", {
                "stage": stage, "generation": generation,
                "completed_generations": len(lineage) - 1,
                "updated_at": datetime.now().isoformat(timespec="seconds"),
            })
    while True:
        completed = len(lineage) - 1
        if completed >= args.steps:
            save_progress("complete", completed)
            # Preserve legacy metadata when resuming, but never call a judge.
            return lineage, lineage[-1].get("novelty") or {"answer": "NOT_EVALUATED"}
        generation = completed + 1
        save_progress("planning", generation)
        traces = checkpoint_dir / "model_calls" if checkpoint_dir is not None else None
        selection_path = checkpoint_dir / f"gen_{generation:03d}_selection.json" if checkpoint_dir is not None else None
        plan = None
        selection = read_json(selection_path) if selection_path is not None and selection_path.exists() else None
        if selection is not None:
            plan, operation, embedding = selection.get("plan"), selection["operation"], selection["embedding"]
            print(f"[resume] reusing generation {generation} mechanism and embedding", file=sys.stderr, flush=True)
        elif args.operation_policy == "guided":
            plan = evolve.plan_evolution_step(
                caller=caller, current=current, discipline=args.discipline,
                scenario_text=scenario, model=args.model, strip_fence=evolve._strip_code_fence,
                baseline_mechanisms=base.get("baseline_mechanisms", []),
                baseline_assumptions=base.get("baseline_assumptions", []),
                scientific_constraints=base.get("scientific_constraints", []),
                prior_mechanisms=[
                    str((item.get("evolution_contract") or {}).get("scientific_mechanism", ""))
                    for item in lineage[1:]
                ],
                assumption_mode=args.assumption_mode,
                max_static_inputs=args.max_static_input_dim,
                max_ode_states=args.max_ode_state_dim,
                dimension_track=base.get("dimension_track") or base.get("dimension_class"),
                trace_path=traces / f"gen_{generation:03d}_plan.jsonl" if traces is not None else None,
                strict_response_contract=getattr(args, "strict_response_contract", False),
            )
            operation = plan["operation"]
        else:
            operation = "change_assumption" if rng.random() < args.p_assumption else "add_term"
        if selection is None:
            embedding = evolve.sample_embedding_pattern(
                rng, current, operation, args.assumption_mode, evolution_plan=plan
            )
            if selection_path is not None:
                _write_json(selection_path, {
                    "plan": plan, "operation": operation, "embedding": embedding,
                    "rng_state_after": rng.getstate(),
                })
        save_progress("evolving", generation)
        print(f"[gen {generation}/{args.steps}] {operation}; embedding={embedding['id']}",
              file=sys.stderr, flush=True)
        strict_response = bool(getattr(args, "strict_response_contract", False)) and (
            selection is None or bool((plan or {}).get("response_change"))
        )
        child = evolve.evolve_once(
            caller=caller, current=current, operation=operation, discipline=args.discipline,
            scenario_text=scenario, model=args.model, strip_fence=evolve._strip_code_fence,
            assumption_mode=args.assumption_mode, max_static_inputs=args.max_static_input_dim,
            max_ode_states=args.max_ode_state_dim, difficulty_feedback=feedback,
            dimension_track=base.get("dimension_track") or base.get("dimension_class"),
            mechanism_profile=base.get("mechanism_profile") or None,
            evolution_plan=plan,
            embedding_pattern=embedding,
            trace_path=traces / f"gen_{generation:03d}_equation.jsonl" if traces is not None else None,
            strict_response_contract=strict_response,
        )
        lineage.append(evolve._record(child, base_id, generation, operation, scenario))
        current = child
        save_progress("evolved", generation)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--discipline")
    p.add_argument("--steps", type=int, default=5)
    p.add_argument("--max-steps", type=int, default=15)
    p.add_argument("--max-lineage-attempts", type=int, default=2)
    p.add_argument("--n-total", type=int, default=5000)
    p.add_argument("--p-assumption", type=float, default=0.5)
    p.add_argument("--operation-policy", choices=["guided", "random"], default="guided")
    p.add_argument("--embedding-policy", choices=["random"], default="random")
    p.add_argument("--assumption-mode", choices=["core", "extended"], default="extended")
    p.add_argument("--max-static-input-dim", type=int, default=4)
    p.add_argument("--max-ode-state-dim", type=int, default=4)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--provider", choices=["anthropic", "openrouter", "openai"], default="anthropic")
    p.add_argument("--base-url")
    p.add_argument("--auth-source", choices=["auto", "api_key", "auth_token"], default="auto")
    p.add_argument("--model", default="claude-opus-4-7")
    p.add_argument("--spec-model")
    p.add_argument("--novelty-model")
    p.add_argument("--cli-path")
    p.add_argument("--spec-max-turns", type=int, default=18)
    p.add_argument("--observable-terminal-window-fraction", type=float, default=0.20)
    p.add_argument("--observable-terminal-flatness-ratio", type=float, default=0.02)
    p.add_argument("--strict-response-contract", action=argparse.BooleanOptionalAction, default=True,
                   help="require structured shortcut/response/diagnostic fields for new guided generations")
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--resume", action="store_true", help="Resume the latest compatible lineage checkpoint")
    args = p.parse_args(argv)
    if not (1 <= args.steps <= args.max_steps and args.max_lineage_attempts >= 1 and args.n_total >= 2):
        p.error("need max_steps >= steps >= 1, positive attempts and at least two points")
    if not 0 < args.observable_terminal_window_fraction < 0.5:
        p.error("terminal window fraction must be between 0 and 0.5")
    if args.observable_terminal_flatness_ratio < 0:
        p.error("terminal flatness ratio must be non-negative")
    usable = evolve._load_usable_equations(Path(args.input))
    base = evolve._normalize_base_equation(evolve._select_equation(usable, args.id, False))
    base_id = evolve._eq_id(base)
    args.discipline = args.discipline or base.get("discipline") or "science"
    out_dir = latest_run(args.output_dir) if args.resume else None
    manifest = {
        "base_id": base_id, "discipline": args.discipline, "seed": args.seed,
        "minimum_steps": args.steps, "max_steps": args.max_steps,
        "total_points": args.n_total, "selection": "numeric validity; observable variation is diagnostic; novelty disabled",
        "evolution": "mechanism-guided natural freedom expansion", "solver_evaluated": False,
    }
    resume_config = {key: value for key, value in vars(args).items() if key not in {"input", "output_dir", "resume"}}
    if out_dir is not None:
        previous = read_json(out_dir / "manifest.json")
        for key in ("base_id", "discipline", "seed", "minimum_steps", "max_steps", "total_points"):
            if previous.get(key) != manifest[key]:
                raise ValueError(f"Resume configuration differs at {key}: {out_dir}")
        previous_resume_config = previous.get("resume_config", resume_config)
        # Older lineage manifests predate this strict contract switch.  Their
        # behavior is equivalent to the current default, so keep their
        # checkpoints resumable after the field was introduced.
        if "strict_response_contract" not in previous_resume_config:
            previous_resume_config["strict_response_contract"] = True
        if previous_resume_config != resume_config:
            raise ValueError(f"Resume requires the same lineage configuration: {out_dir}")
        result_path = out_dir / "final_result.json"
        if result_path.exists():
            result = read_json(result_path)
            candidate = result.get("candidate", {})
            candidate_spec = Path(candidate.get("spec", ""))
            if (result.get("status") == "candidate_generated"
                    and (out_dir / "final_spec.json").is_file()
                    and candidate_spec.is_file()
                    and Path(candidate.get("data_csv", "")).is_file()
                    and read_jsonl(candidate_spec.parent / "accepted_lineage.jsonl")):
                print(f"Already complete: {out_dir}", file=sys.stderr)
                return
        failure = candidate_failure(out_dir)
        if failure is not None:
            raise SystemExit(f"Candidate previously failed numerically; skip this scenario: {failure['error']}")
    else:
        out_dir = args.output_dir.resolve() / f"candidate_{base_id}_{datetime.now():%Y%m%d-%H%M%S-%f}"
    caller = build_model_caller(args.provider, base_url=args.base_url, auth_source=args.auth_source)
    out_dir.mkdir(parents=True, exist_ok=True)
    _write_json(out_dir / "manifest.json", manifest | {"resume_config": resume_config})
    audit = out_dir / "lineage_attempts.jsonl"
    rng, feedback = random.Random(args.seed), None
    outcomes = attempt_outcomes(out_dir)
    for attempt in range(1, args.max_lineage_attempts + 1):
        if args.resume and outcomes.get(attempt, {}).get("status") == "reject_invalid_evolution":
            print(f"[resume] lineage {attempt} already rejected; trying the next attempt", file=sys.stderr)
            continue
        attempt_dir = out_dir / f"lineage_attempt_{attempt:02d}"
        attempt_dir.mkdir(exist_ok=True)
        # Historical errors remain in lineage_attempts.jsonl; this file is the current invocation's failure.
        failure_path = attempt_dir / "failure.json"
        if failure_path.exists():
            failure_path.rename(attempt_dir / f"failure_{datetime.now():%Y%m%d-%H%M%S-%f}.json")
        print(f"[lineage {attempt}/{args.max_lineage_attempts}]", file=sys.stderr, flush=True)
        try:
            lineage, novelty = _lineage(base, base_id, caller, args, rng, feedback, checkpoint_dir=attempt_dir)
            final = dict(lineage[-1])
            observation_history = [
                {"generation": row["generation"], "plan": row.get("evolution_plan"),
                 "contract": row.get("evolution_contract"),
                 "range_suggestions": row.get("new_symbol_range_suggestions", {})}
                for row in lineage[1:]
            ]
            final["mechanism_observation_history"] = observation_history
            _write_json(attempt_dir / "mechanism_observation_history.json", observation_history)
            _write_json(attempt_dir / "novelty.json", novelty)
            planned_spec = attempt_dir / "planned_spec.json"
            if planned_spec.exists():
                spec = read_json(planned_spec)
            else:
                spec = _plan_spec(final, lineage[-2], args)
                _write_json(planned_spec, spec)
            spec.update(discipline=args.discipline, scenario_text=base.get("scenario_text", ""))
            spec, csv_path = _generate(spec, base_id, len(lineage) - 1, attempt_dir / "candidate_data", args.seed + attempt, args.n_total)
            values = np.loadtxt(csv_path, delimiter=",", skiprows=1, ndmin=2)
            nonfinite = ~np.isfinite(values)
            if len(values) != args.n_total or nonfinite.any():
                diagnostics = {"data_csv": str(csv_path), "expected_rows": args.n_total,
                               "actual_rows": len(values), "nonfinite_rows": int(nonfinite.any(axis=1).sum()),
                               "nonfinite_values": int(nonfinite.sum())}
                raise CandidateDataError(
                    f"candidate data invalid: {len(values)}/{args.n_total} rows, "
                    f"{diagnostics['nonfinite_rows']} rows contain NaN or infinity",
                    diagnostics=diagnostics,
                )
            observable = _observable_gate(spec, [csv_path], args)
            _write_json(attempt_dir / "observable_gate.json", observable)
            spec["mechanism_observation_history"] = observation_history
            spec["evolution_provenance"] = {
                "dimension_track": evolve._inherited_dimension_track(final),
                "mechanism_profile": final.get("mechanism_profile", {}),
                "baseline_mechanisms": base.get("baseline_mechanisms", []),
                "baseline_assumptions": base.get("baseline_assumptions", []),
                "scientific_constraints": base.get("scientific_constraints", []),
                "refinement_agenda": base.get("refinement_agenda", []),
                "evolution_contracts": [item.get("evolution_contract") for item in lineage[1:]],
            }
            response_reports = _response_reports(spec, final, lineage[-2] if len(lineage) >= 2 else None, args)
            spec.update(response_reports)
            spec["finalization"] = {"mode": "candidate", "accepted_generations": len(lineage) - 1,
                "novelty": novelty, "total_points": args.n_total, "evaluation_status": "not_evaluated"}
            spec_path = attempt_dir / "candidate_spec.json"
            _write_json(spec_path, spec)
            _write_lineage(attempt_dir / "accepted_lineage.jsonl", lineage)
            evolve._build_lineage_xlsx(attempt_dir / "accepted_lineage.xlsx", lineage)
            record = {"attempt": attempt, "status": "candidate_generated", "novelty": novelty,
                "observable_gate": observable, "candidate": {"spec": str(spec_path), "data_csv": str(csv_path), "n_points": args.n_total}}
            _write_jsonl(audit, record)
            _write_json(out_dir / "final_spec.json", spec)
            _write_json(out_dir / "final_result.json", record)
            print(f"CANDIDATE: {args.n_total} points; {out_dir}", file=sys.stderr)
            return
        except Exception as exc:
            status = ("candidate_error" if isinstance(exc, CandidateDataError) else
                      "request_error" if isinstance(exc, ModelServiceError) else
                      "reject_invalid_evolution" if isinstance(exc, evolve.EvolvedEquationValidationError)
                      else "pipeline_error")
            failure = {"attempt": attempt, "status": status,
                       "retryable": isinstance(exc, ModelServiceError) and exc.retryable,
                       "error": f"{type(exc).__name__}: {exc}",
                       "progress": str(attempt_dir / "progress.json"),
                       "model_calls": str(attempt_dir / "model_calls")}
            for attribute in ("trace", "qa_history"):
                details = getattr(exc, attribute, None)
                if details is not None:
                    failure[attribute] = details
            if isinstance(exc, CandidateDataError):
                failure.update(failure_kind="invalid_numeric_data", data_check=exc.diagnostics)
                progress_path = attempt_dir / "progress.json"
                progress = read_json(progress_path) if progress_path.exists() else {}
                _write_json(progress_path, progress | {"stage": "candidate_failed",
                    "updated_at": datetime.now().isoformat(timespec="seconds")})
            _write_json(attempt_dir / "failure.json", failure)
            _write_jsonl(audit, failure)
            if isinstance(exc, CandidateDataError):
                # End this scenario, not another lineage attempt from the same E0.
                raise SystemExit(f"Candidate failed numerically; skip this scenario. Audit: {audit}: {exc}") from exc
            if isinstance(exc, evolve.EvolvedEquationValidationError):
                # Another lineage may choose a valid mechanism; the batch skips this seed if all attempts fail.
                continue
            raise RuntimeError(f"Pipeline failed; inspect {audit}: {exc}") from exc
    raise SystemExit(f"No acceptable candidate after {args.max_lineage_attempts} lineages. Audit: {audit}")


if __name__ == "__main__":
    main()
