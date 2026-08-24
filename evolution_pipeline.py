"""Final-difficulty-controlled SRBench evolution pipeline.

The selection unit is a complete lineage: gen0 -> ... -> genN -> novelty check
-> data/spec -> external SR solver.  Only the solver's clipped test R² on an
independent hidden test CSV decides whether a final task is too easy.  The
solver command receives {train}, {test}, {spec}, and {output}, and must print
JSON containing raw_test_r2 (or test_r2).
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import random
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import equation_evolve as evolve
from harbor_task_builder import build_task
import novelty_check
from data_generator.generate_from_spec import generate
from data_spec_agent_sdk import _attach_ode_benchmark_metadata, plan_data_generation, validate_sampling_replan
from model_provider import build_model_caller


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, value: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")


def _plan_spec(record: dict, parent: dict | None, args: argparse.Namespace, *, replan: dict | None = None) -> dict:
    spec = plan_data_generation(
        record, args.discipline, provider=args.provider, base_url=args.base_url,
        auth_source=args.auth_source, model=args.spec_model or args.model,
        cli_path=args.cli_path, parent=parent, sampling_replan=replan,
        k_sigma=args.k_sigma, max_turns=args.spec_max_turns,
    )
    return _attach_ode_benchmark_metadata(spec, record)


def _generate(spec: dict, base_id: str, generation: int, output_dir: Path, seed: int, n_total: int) -> tuple[dict, Path]:
    local = dict(spec)
    local.update({"record_id": base_id, "generation": generation, "_n_total": n_total})
    result = generate(local, output_dir, seed=seed, verbose=False)
    return local, Path(result["csv_path"])


def _parse_solver_output(text: str) -> dict[str, Any]:
    for line in reversed(text.splitlines()):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("solver stdout must include one JSON result line")


def _score(command_template: str, train: Path, test: Path, spec: Path, output: Path,
           task: Path | None = None) -> dict[str, Any]:
    command = command_template.format(train=str(train), test=str(test), spec=str(spec),
                                      output=str(output), task=str(task) if task else "")
    proc = subprocess.run(command, shell=True, text=True, capture_output=True)
    if proc.returncode:
        raise RuntimeError(f"solver command exited {proc.returncode}: {proc.stderr[-1000:]}")
    report = _parse_solver_output(proc.stdout)
    raw = report.get("raw_test_r2", report.get("test_r2"))
    if not isinstance(raw, (int, float)) or not math.isfinite(raw):
        raise ValueError("solver JSON must contain finite raw_test_r2 or test_r2")
    report.update({"command": command, "raw_test_r2": float(raw),
                   "clipped_test_r2": max(-1.0, min(float(raw), 1.0)),
                   "stderr": proc.stderr})
    return report


def _export_harbor(template: Path | None, train: Path, test: Path, spec: Path,
                   output_dir: Path, name: str) -> Path | None:
    if template is None:
        return None
    return build_task(template, train, test, spec, output_dir, name)


def _range_only_replan(final: dict, parent: dict, baseline: dict, report: dict,
                       args: argparse.Namespace) -> dict:
    """Ask the Spec Agent for ranges, then apply only those ranges to baseline.

    The baseline spec remains authoritative; an agent-produced replan cannot
    replace the whole spec, even if it was prompted with the lineage record.
    """
    proposal = _plan_spec(final, parent, args,
                          replan={"baseline_spec": baseline, "difficulty_report": report})
    out = copy.deepcopy(baseline)
    proposed_axes = proposal.get("independent_variables", []) or []
    baseline_axes = out.get("independent_variables", []) or []
    if len(proposed_axes) != len(baseline_axes):
        raise ValueError("sampling replan changed the number of independent variables")
    for old, new in zip(baseline_axes, proposed_axes):
        if old.get("symbol") != new.get("symbol"):
            raise ValueError("sampling replan changed an independent-variable symbol")
        old["range"] = new.get("range")
    validate_sampling_replan(baseline, out)
    return out


def _feedback(score: dict, threshold: float) -> str:
    return (
        f"The preceding complete lineage produced a task the designated solver solved too easily "
        f"(clipped test R²={score['clipped_test_r2']:.6g} > {threshold:.6g}). Restart from gen0. "
        "Every child must be a scientifically consequential successor of its immediate parent: "
        "do not use coefficient-only perturbations, reparameterization, or cosmetic algebra. "
        "Introduce an observable mechanism, coupling, saturation, threshold, regime, or justified state/condition refinement."
    )


def _lineage(base: dict, base_id: str, caller: Any, args: argparse.Namespace,
             rng: random.Random, feedback: str | None) -> tuple[list[dict], dict]:
    scenario = base.get("scenario_text", "")
    lineage = [evolve._record(base, base_id, 0, "base", scenario)]
    current = base
    novelty: dict[str, Any] | None = None
    for generation in range(1, args.max_steps + 1):
        operation = "change_assumption" if rng.random() < args.p_assumption else "add_term"
        print(f"[gen {generation}/{args.steps}] {operation}", file=sys.stderr, flush=True)
        child = evolve.evolve_once(
            caller=caller, current=current, operation=operation, discipline=args.discipline,
            scenario_text=scenario, model=args.model, strip_fence=evolve._strip_code_fence,
            assumption_mode=args.assumption_mode, max_static_inputs=args.max_static_input_dim,
            max_ode_states=args.max_ode_state_dim, difficulty_feedback=feedback,
        )
        lineage.append(evolve._record(child, base_id, generation, operation, scenario))
        current = child
        if generation >= args.steps:
            print(f"[novelty at gen {generation}]", file=sys.stderr, flush=True)
            novelty = novelty_check.check_novelty(
                caller, lineage[-1], args.discipline, scenario, args.novelty_model or args.model, base=base,
            )
            lineage[-1]["novelty"] = novelty
            if novelty.get("answer") == "Yes":
                return lineage, novelty
    return lineage, novelty or {"answer": "No", "reasoning": "max_steps reached without a novelty verdict"}


def main() -> None:
    p = argparse.ArgumentParser(description="Build gen0-to-genN lineages and reject final tasks that an SR solver solves too easily.")
    p.add_argument("--input", required=True)
    p.add_argument("--id", required=True)
    p.add_argument("--discipline", default=None)
    p.add_argument("--steps", type=int, default=5)
    p.add_argument("--max-steps", type=int, default=None,
                   help="novelty is checked from --steps onward; continue until Yes or this cap (default: steps + 10)")
    p.add_argument("--max-lineage-attempts", type=int, default=4)
    p.add_argument("--easy-r2", type=float, default=0.90)
    p.add_argument("--solver-command", required=True, help="shell template with {train}, {test}, {spec}, {task}, {output}; must print JSON raw_test_r2")
    p.add_argument("--harbor-template", type=Path, default=None,
                   help="known-good Harbor task directory; export each candidate as a Harbor task before scoring")
    p.add_argument("--n-total", type=int, default=5000,
                   help="total points per candidate, split into visible train and hidden test")
    p.add_argument("--test-points", type=int, default=500,
                   help="points withheld from the Harbor agent and used only by its verifier")
    p.add_argument("--p-assumption", type=float, default=0.5)
    p.add_argument("--assumption-mode", choices=["core", "extended"], default="extended")
    p.add_argument("--max-static-input-dim", type=int, default=evolve.MAX_STATIC_INPUTS_DEFAULT)
    p.add_argument("--max-ode-state-dim", type=int, default=evolve.MAX_ODE_STATES_DEFAULT)
    p.add_argument("--k-sigma", type=float, default=5.0)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--provider", choices=["anthropic", "openrouter"], default="anthropic")
    p.add_argument("--base-url", default=None)
    p.add_argument("--auth-source", choices=["auto", "api_key", "auth_token"], default="auto")
    p.add_argument("--model", default="claude-opus-4-7")
    p.add_argument("--spec-model", default=None)
    p.add_argument("--novelty-model", default=None)
    p.add_argument("--cli-path", default=None)
    p.add_argument("--spec-max-turns", type=int, default=18)
    p.add_argument("--output-dir", default=None)
    args = p.parse_args()
    if args.max_steps is None:
        args.max_steps = args.steps + 10
    if (args.steps < 1 or args.max_steps < args.steps or args.max_lineage_attempts < 1
            or args.n_total < 2 or args.test_points < 2 or args.test_points >= args.n_total):
        raise SystemExit("need max_steps >= steps >= 1 and 2 <= test_points < n_total")
    train_points = args.n_total - args.test_points
    if not -1 <= args.easy_r2 <= 1:
        raise SystemExit("--easy-r2 must be in [-1, 1]")

    usable = evolve._load_usable_equations(Path(args.input))
    base = evolve._normalize_base_equation(evolve._select_equation(usable, args.id, False))
    base_id = evolve._eq_id(base)
    args.discipline = args.discipline or base.get("discipline") or "science"
    caller = build_model_caller(args.provider, base_url=args.base_url, auth_source=args.auth_source)
    root = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent / "outputs" / "Final_Difficulty_Evolution"
    out_dir = root / f"final_{base_id}_{datetime.now():%Y%m%d-%H%M%S}"
    out_dir.mkdir(parents=True, exist_ok=False)
    _write_json(out_dir / "manifest.json", {"base_id": base_id, "discipline": args.discipline,
        "source_input": str(Path(args.input).resolve()), "selection": "final external solver clipped test R²",
        "minimum_steps": args.steps, "max_steps": args.max_steps, "easy_r2": args.easy_r2,
        "total_points": args.n_total, "train_points": train_points,
        "hidden_test_points": args.test_points, "seed": args.seed,
        "solver_command_template": args.solver_command})
    audit = out_dir / "lineage_attempts.jsonl"
    rng, feedback = random.Random(args.seed), None

    for attempt in range(1, args.max_lineage_attempts + 1):
        attempt_dir = out_dir / f"lineage_attempt_{attempt:02d}"
        attempt_dir.mkdir()
        print(f"\n[lineage attempt {attempt}/{args.max_lineage_attempts}]", file=sys.stderr, flush=True)
        try:
            lineage, novelty = _lineage(base, base_id, caller, args, rng, feedback)
            final = lineage[-1]
            _write_json(attempt_dir / "novelty.json", novelty)
            if novelty.get("answer") != "Yes":
                _write_jsonl(audit, {"attempt": attempt, "status": "reject_not_novel", "novelty": novelty})
                feedback = "The prior gen5 candidate was judged recitable/not novel. Use genuine observable mechanisms, not a textbook restatement."
                continue
            initial = _plan_spec(final, lineage[-2], args)
            # The DataGenSpec is the Harbor exporter input as well as the
            # generator input.  Preserve scientific context without exposing
            # the hidden formula or any parameter values in instruction.md.
            initial["discipline"] = args.discipline
            initial["scenario_text"] = base.get("scenario_text", "")
            final_generation = len(lineage) - 1
            initial, train = _generate(initial, base_id, final_generation, attempt_dir / "train_initial", args.seed + attempt, train_points)
            _, test = _generate(initial, base_id, final_generation, attempt_dir / "test_initial", args.seed + 10000 + attempt, args.test_points)
            initial_path = attempt_dir / "initial_spec.json"
            _write_json(initial_path, initial)
            initial_task = _export_harbor(args.harbor_template, train, test, initial_path,
                                          attempt_dir / "harbor_tasks", f"{base_id}_attempt{attempt}_initial")
            score = _score(args.solver_command, train, test, initial_path,
                           attempt_dir / "solver_initial.json", initial_task)
            _write_json(attempt_dir / "solver_initial.json", score)
            record: dict[str, Any] = {"attempt": attempt, "novelty": novelty,
                "initial": {"spec": str(initial_path), "train_csv": str(train), "test_csv": str(test), "solver": score}}
            if initial_task is not None:
                record["initial"]["harbor_task"] = str(initial_task)
            chosen_spec, chosen_train, chosen_test, chosen_score = initial, train, test, score
            if score["clipped_test_r2"] > args.easy_r2:
                replan = _range_only_replan(final, lineage[-2], initial, score, args)
                replan, replan_train = _generate(replan, base_id, final_generation, attempt_dir / "train_replanned", args.seed + 1000 + attempt, train_points)
                _, replan_test = _generate(replan, base_id, final_generation, attempt_dir / "test_replanned", args.seed + 11000 + attempt, args.test_points)
                replan_path = attempt_dir / "replanned_spec.json"
                _write_json(replan_path, replan)
                replan_task = _export_harbor(args.harbor_template, replan_train, replan_test, replan_path,
                                              attempt_dir / "harbor_tasks", f"{base_id}_attempt{attempt}_replanned")
                replan_score = _score(args.solver_command, replan_train, replan_test, replan_path,
                                      attempt_dir / "solver_replanned.json", replan_task)
                _write_json(attempt_dir / "solver_replanned.json", replan_score)
                record["sampling_replan"] = {"spec": str(replan_path), "train_csv": str(replan_train), "test_csv": str(replan_test), "solver": replan_score}
                if replan_task is not None:
                    record["sampling_replan"]["harbor_task"] = str(replan_task)
                chosen_spec, chosen_train, chosen_test, chosen_score = replan, replan_train, replan_test, replan_score
            if chosen_score["clipped_test_r2"] > args.easy_r2:
                record["status"] = "reject_too_easy_after_replan"
                _write_jsonl(audit, record)
                feedback = _feedback(chosen_score, args.easy_r2)
                continue
            record["status"] = "accept"
            _write_jsonl(audit, record)
            evolve._build_lineage_xlsx(attempt_dir / "accepted_lineage.xlsx", lineage)
            with (attempt_dir / "accepted_lineage.jsonl").open("w", encoding="utf-8") as f:
                for item in lineage:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            chosen_spec = dict(chosen_spec)
            chosen_spec["finalization"] = {"accepted_generations": len(lineage) - 1, "novelty": novelty,
                "solver_score": chosen_score, "selection_threshold": args.easy_r2,
                "total_points": args.n_total, "train_points": train_points,
                "hidden_test_points": args.test_points,
                "train_csv": str(chosen_train), "hidden_test_csv": str(chosen_test),
                "sampling_replanned": "sampling_replan" in record}
            _write_json(out_dir / "final_spec.json", chosen_spec)
            _write_json(out_dir / "final_result.json", record)
            print(f"ACCEPT: clipped test R²={chosen_score['clipped_test_r2']:.6g}; {out_dir}", file=sys.stderr)
            return
        except Exception as exc:
            _write_jsonl(audit, {"attempt": attempt, "status": "pipeline_error", "error": f"{type(exc).__name__}: {exc}"})
            feedback = "The prior full-lineage attempt failed validation or generation. Keep the next parent-child chain structurally coherent and numerically observable."
            print(f"REJECT pipeline error: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
    raise SystemExit(f"No acceptable final task after {args.max_lineage_attempts} full lineages. Audit: {audit}")


if __name__ == "__main__":
    main()
