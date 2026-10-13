#!/usr/bin/env python3
"""Collect a requested number of biology/physics candidates using existing stages.

One scheduler owns the run directory. Scientific decisions stay in the normal
pipeline. Rejected or textually duplicated candidates are replaced with new
gen0s up to a finite round budget; transient request errors can be deferred.
"""
from __future__ import annotations

import argparse
import ast
import csv
import fcntl
import hashlib
import json
import shutil
import sys
import threading
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path

from srbench.common.io import append_jsonl as _append_jsonl, read_jsonl as _read_jsonl
from srbench.common.contracts import noiseless_spec
from srbench.generation.executors import JobTimeoutError, run_local
from srbench.generation.checkpoints import latest_run, attempt_outcomes, candidate_failure

SUBJECTS = ("biology", "physics")


def copy_clean_data(source, destination, spec):
    """Publish clean labels when resuming a candidate from older checkpoints."""
    noisy_columns = {str(spec[name]) + "_noisy" for name in
                     ("benchmark_output", "dependent_variable") if spec.get(name)}
    destination = Path(destination)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with Path(source).open(encoding="utf-8", newline="") as source_file, \
            temporary.open("w", encoding="utf-8", newline="") as target_file:
        reader = csv.DictReader(source_file)
        if not reader.fieldnames:
            raise ValueError(f"candidate CSV has no header: {source}")
        fields = [name for name in reader.fieldnames if name not in noisy_columns]
        writer = csv.DictWriter(target_file, fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(reader)
    temporary.replace(destination)


def publish_candidate(root, subject, number, run_dir, result, equation):
    """Expose accepted results without requiring the internal checkpoint layout."""
    destination = root / "01_generated" / f"{subject}_{number:03d}"
    destination.mkdir(parents=True, exist_ok=True)
    _write_json(destination / "equation.json", equation)
    spec = noiseless_spec(json.loads((run_dir / "final_spec.json").read_text(encoding="utf-8")))
    if "finalization" in spec:
        spec["finalization"].pop("data_csv", None)
    _write_json(destination / "spec.json", spec)
    copy_clean_data(result["candidate"]["data_csv"], destination / "data.csv", spec)
    lineage = Path(result["candidate"]["spec"]).parent / "accepted_lineage.jsonl"
    shutil.copy2(lineage, destination / "lineage.jsonl")
    # Publish a self-contained audit snapshot, including incomplete prior
    # attempts, generation selections, model traces, specs and diagnostics.
    # Exclude numeric data/images already published separately.
    archive = destination / "lineage_archive"
    shutil.copytree(run_dir, archive, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("candidate_data", "*.xlsx", "__pycache__"))
    _write_json(archive / "archive_manifest.json", {
        "schema_version": 1,
        "source_run": str(run_dir),
        "accepted_attempt": lineage.parent.name,
        "files": sorted(str(path.relative_to(archive)) for path in archive.rglob("*")
                        if path.is_file() and path.name != "archive_manifest.json"),
        "note": "Paths inside historical records are original provenance; use archive-relative files for inspection. Numeric data is published as ../data.csv.",
    })
    return {name: str((destination / filename).relative_to(root)) for name, filename in {
        "equation_path": "equation.json", "spec": "spec.json", "data_csv": "data.csv", "lineage": "lineage.jsonl", "lineage_archive": "lineage_archive",
    }.items()}


def publish_index(root):
    rows = [item for subject in SUBJECTS for item in _read_jsonl(root / "_checkpoints" / subject / "formulas.jsonl")]
    path = root / "01_generated" / "index.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    temporary.replace(path)


def candidate_counts(root):
    return {subject: len(_read_jsonl(root / "_checkpoints" / subject / "formulas.jsonl")) for subject in SUBJECTS}


def _print_progress(subject: str, round_index: int, accepted: int, target: int,
                    pending_jobs, started_at: float, queued: int | None = None) -> None:
    """Print a bounded scheduler heartbeat while model workers are waiting."""
    elapsed = int(max(0.0, time.monotonic() - started_at))
    active = []
    for job in pending_jobs:
        _, equation_id, _, _, log = job
        try:
            age = max(0, int(time.time() - log.stat().st_mtime))
            active.append(f"{equation_id}:log_age={age}s")
        except FileNotFoundError:
            active.append(f"{equation_id}:log=pending")
    details = f" active_jobs={','.join(active[:3])}" if active else ""
    if len(active) > 3:
        details += f" (+{len(active) - 3} more)"
    queue = f" queued={queued}" if queued is not None else ""
    print(
        f"[progress] subject={subject} round={round_index + 1:03d} "
        f"accepted={accepted}/{target} active={len(active)} elapsed={elapsed}s{queue}{details}",
        file=sys.stderr,
        flush=True,
    )


def formula_key(equation: dict) -> str:
    """Conservative duplicate key; not a test of algebraic equivalence.

    Ignore whitespace, redundant parentheses, parameter values and initial
    conditions; retain symbol names, roles and every ODE state equation.
    """
    def expression_key(expression: str) -> str:
        return ast.dump(ast.parse(expression.strip(), mode="eval"), include_attributes=False)

    ode = equation.get("ode_system") or {}
    content = {
        "family": equation.get("model_family"), "type": equation.get("equation_type"),
        "target": equation.get("target_symbol"), "rhs": expression_key(equation["expression"]),
        "roles": sorted(zip(equation["symbols"], equation["symbol_properties"])),
        "time": ode.get("time_symbol"), "target_state": ode.get("target_state"),
        "states": sorted((state["symbol"], expression_key(state["rhs"])) for state in ode.get("states", [])),
    }
    return hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()


def job_seed(args, subject: str, round_index: int, slot: int = 0) -> int:
    # 64 seeds per job reserve space for the pipeline's per-attempt offsets.
    # Subject indexes are stable even when the two subjects run separately.
    position = (SUBJECTS.index(subject) * args.max_rounds + round_index) * (args.batch_size + 1) + slot
    return args.seed + 64 * position


def _write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def _run(command: list[str], log_path: Path, **kwargs) -> int:
    return run_local(command, log_path, **kwargs)


def provider_flags(args) -> list[str]:
    flags = ["--provider", args.provider, "--model", args.model, "--auth-source", args.auth_source]
    if args.base_url:
        flags += ["--base-url", args.base_url]
    return flags


def generation_command(args, subject: str, round_index: int, round_dir: Path, count: int) -> list[str]:
    command = [sys.executable, "-m", "srbench.generation.scenarios", "--subject", subject,
               "--scenarios", str(count), "--n-subfields", str(args.n_subfields),
               "--subfield-source", "fixed", "--equation-mode", "generate",
               "--seed", str(job_seed(args, subject, round_index)),
               "--output-dir", str(round_dir / "gen0"), "--run-name", subject,
               *provider_flags(args)]
    if (round_dir / "gen0" / "Equations" / subject / "run_meta.json").exists():
        command.append("--resume")
    return command


def reuse_generation(source_root: Path, subject: str, round_index: int,
                     round_dir: Path) -> tuple[int, str]:
    """Copy a prior gen0 checkpoint so only the current evolution is rerun.

    A scenario JSONL is descriptive metadata; evolution needs the validated
    Stage-3 equations JSONL.  Keep the source immutable and copy only the
    relevant checkpoint files into the new run.
    """
    source_root = Path(source_root).expanduser().resolve()
    source_parent = source_root / "_checkpoints" / subject
    source_rounds = sorted(source_parent.glob(f"round_*/gen0/Equations/{subject}/equations.jsonl"))
    if not source_rounds:
        raise FileNotFoundError(
            f"No reusable equations for {subject} under {source_root}; "
            "pass the original v7 run directory, not only Scenarios/scenarios.jsonl."
        )
    # Prefer the matching source round. If the old run stopped earlier, reuse
    # its last equation batch as replacement seeds; this keeps the scenario
    # distribution fixed while allowing a transient/invalid lineage to retry.
    requested = source_parent / f"round_{round_index + 1:03d}" / "gen0" / "Equations" / subject / "equations.jsonl"
    source_equations = requested if requested.is_file() else source_rounds[-1]
    source_round = source_equations.parents[3]
    destination_gen0 = round_dir / "gen0"
    destination_equations = destination_gen0 / "Equations" / subject / "equations.jsonl"
    destination_equations.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_equations, destination_equations)
    for relative in (
        Path("Scenarios") / subject / "scenarios.jsonl",
        Path("Scenarios") / subject / "subfields.json",
        Path("Equations") / subject / "progress.json",
        Path("Equations") / subject / "run_meta.json",
    ):
        source_file = source_round / relative
        if source_file.is_file():
            target_file = destination_gen0 / relative
            target_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_file, target_file)
    rows = _read_jsonl(destination_equations)
    if not rows:
        raise ValueError(f"Reusable equation file is empty: {source_equations}")
    return len(rows), str(source_equations)


def evolution_command(args, subject: str, round_index: int, index: int,
                      equations: Path, equation_id: str, output: Path) -> list[str]:
    command = [sys.executable, "-m", "srbench.generation.pipeline",
               "--input", str(equations), "--id", equation_id, "--discipline", subject,
               "--steps", str(args.steps), "--max-steps", str(args.max_steps),
               "--max-lineage-attempts", str(args.max_lineage_attempts),
               "--operation-policy", "guided", "--embedding-policy", "random",
               "--assumption-mode", "extended", "--max-static-input-dim", str(args.max_static_input_dim),
               "--max-ode-state-dim", str(args.max_ode_state_dim), "--n-total", str(args.n_total),
               "--seed", str(job_seed(args, subject, round_index, index + 1)),
               "--output-dir", str(output), *provider_flags(args)]
    for name in ("spec_model", "novelty_model", "cli_path"):
        if getattr(args, name):
            command += ["--" + name.replace("_", "-"), getattr(args, name)]
    if getattr(args, "resume", False):
        command.append("--resume")
    return command


def completed_candidate(output: Path) -> tuple[Path, dict, dict] | None:
    for result_path in sorted(output.glob("candidate_*/final_result.json")):
        result = json.loads(result_path.read_text(encoding="utf-8"))
        if result.get("status") != "candidate_generated":
            continue
        candidate_spec = Path(result["candidate"]["spec"])
        lineage = _read_jsonl(candidate_spec.parent / "accepted_lineage.jsonl")
        spec_path = result_path.parent / "final_spec.json"
        if lineage and spec_path.exists() and Path(result["candidate"]["data_csv"]).exists():
            return result_path.parent, lineage[-1], result
    return None


def expected_rejection(output: Path) -> bool:
    # Remote workers may use UTC while older local attempts used local time.
    # Choose the most recently written attempt, not its timestamped filename.
    run = latest_run(output)
    if run is None:
        return False
    attempts = list(attempt_outcomes(run).values())
    # A swallowed API/validation/runtime error must not be reported as a
    # scientific rejection and silently trigger hundreds of new API calls.
    return bool(attempts) and all(item.get("status", "").startswith("reject_") for item in attempts)


def transient_failure(output: Path) -> str | None:
    run = latest_run(output)
    outcomes = attempt_outcomes(run) if run is not None else {}
    item = outcomes[max(outcomes)] if outcomes else {}
    if item.get("status") == "request_error" and item.get("retryable"):
        return item.get("error", "transient model request failure")
    return None


def collect_subject(args, subject: str, root: Path) -> None:
    subject_dir = root / "_checkpoints" / subject
    subject_dir.mkdir(parents=True, exist_ok=True)
    accepted_path = subject_dir / "formulas.jsonl"
    accepted = _read_jsonl(accepted_path)
    known = {item["formula_key"] for name in args.subjects for item in _read_jsonl(root / "_checkpoints" / name / "formulas.jsonl")}
    ledger = subject_dir / "attempts.jsonl"
    terminal = {item["job_id"] for item in _read_jsonl(ledger)
                if item.get("status") in {"accepted", "rejected", "duplicate", "skipped"}}
    terminal |= {item["job_id"] for item in accepted}
    consecutive_failures = 0

    def defer(job, reason):
        nonlocal consecutive_failures
        consecutive_failures += 1
        _append_jsonl(ledger, {"job_id": job[2], "status": "deferred", "error": reason, "log": str(job[4])})
        print(f"Deferred {job[2]}: {reason}. Checkpoints retained; other jobs may continue.",
              file=sys.stderr, flush=True)
        if consecutive_failures >= getattr(args, "max_consecutive_request_errors", 3):
            raise RuntimeError(f"{consecutive_failures} consecutive transient failures; "
                               "stopping new requests. Check the model endpoint before resuming.")

    for round_index in range(args.max_rounds):
        if len(accepted) >= args.target_per_subject:
            break
        round_dir = subject_dir / f"round_{round_index + 1:03d}"
        round_dir.mkdir(exist_ok=True)
        plan_path = round_dir / "round.json"
        if not plan_path.exists():
            count = max(args.n_subfields, min(args.batch_size, args.target_per_subject - len(accepted)))
            _write_json(plan_path, {"n_scenarios": count, "seed": job_seed(args, subject, round_index)})
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        generated_marker = round_dir / "generation_complete.json"
        equations = round_dir / "gen0" / "Equations" / subject / "equations.jsonl"
        if not generated_marker.exists():
            if getattr(args, "reuse_from", None) is not None:
                try:
                    n_equations, source = reuse_generation(
                        args.reuse_from, subject, round_index, round_dir)
                except (FileNotFoundError, ValueError) as exc:
                    raise RuntimeError(str(exc)) from exc
                _write_json(generated_marker, {
                    "n_equations": n_equations,
                    "reused": True,
                    "source": source,
                })
            else:
                command = generation_command(args, subject, round_index, round_dir, plan["n_scenarios"])
                log = round_dir / "generation.log"
                if _run(command, log) != 0:
                    raise RuntimeError(f"Generation failed; repair the error and resume. Log: {log}")
                rows = _read_jsonl(equations)
                if not rows:
                    raise RuntimeError(f"No gen0 equations were produced. Log: {log}")
                _write_json(generated_marker, {"n_equations": len(rows)})
        rows = _read_jsonl(equations)
        if len(rows) > args.batch_size:
            raise RuntimeError(f"Generation exceeded the planned seed allocation: {equations}")
        jobs = []
        for index, equation in enumerate(rows):
            equation_id = equation["scenario_id"]
            job_id = f"{args.run_name}/{subject}/{round_index + 1:03d}/{equation_id}"
            if job_id in terminal:
                continue
            output = round_dir / "evolved" / f"job_{index + 1:03d}"
            log = round_dir / f"evolve_{index + 1:03d}.log"
            jobs.append((index, equation_id, job_id, output, log))

        cancelled = threading.Event()

        def execute(job):
            index, equation_id, _, output, log = job
            candidate = completed_candidate(output)
            if candidate is not None:
                return candidate, 0
            run = latest_run(output)
            if run is not None and candidate_failure(run) is not None:
                # A saved numeric failure needs no new worker or model call.
                return None, 1
            command = evolution_command(args, subject, round_index, index, equations, equation_id, output)
            if getattr(args, "executor", "local") == "daytona":
                from srbench.generation.executors import run_daytona
                returncode = run_daytona(command, log, args, cancelled=cancelled)
            else:
                returncode = _run(command, log, cancelled=cancelled, timeout=getattr(args, "job_timeout", 14400))
            return completed_candidate(output), returncode

        def collect(job, outcome):
            nonlocal consecutive_failures
            # Only this coordinator writes the shared ledgers and public IDs.
            index, _, job_id, output, log = job
            candidate, returncode = outcome
            if candidate is None:
                run = latest_run(output)
                failure = candidate_failure(run) if run is not None else None
                if failure is not None:
                    _append_jsonl(ledger, {"job_id": job_id, "status": "skipped",
                        "reason": "invalid_numeric_data", "error": failure["error"],
                        "attempt": failure.get("attempt"), "data_check": failure.get("data_check", {}),
                        "run_dir": str(run), "log": str(log)})
                    terminal.add(job_id)
                    consecutive_failures = 0
                    print(f"Skipped {job_id}: {failure['error']}. Records retained; continuing to the next scenario.",
                          file=sys.stderr, flush=True)
                    return
                if returncode != 0 and expected_rejection(output):
                    _append_jsonl(ledger, {"job_id": job_id, "status": "rejected", "log": str(log)})
                    terminal.add(job_id)
                    consecutive_failures = 0
                    return
                reason = transient_failure(output)
                if reason and getattr(args, "on_request_error", "defer") == "defer":
                    defer(job, reason)
                    return
                raise RuntimeError(f"Evolution failed or produced incomplete output. Log: {log}")
            consecutive_failures = 0
            run_dir, final, result = candidate
            key = formula_key(final)
            status = "duplicate" if key in known else "accepted"
            if status == "accepted":
                entry = {
                    "job_id": job_id, "subject": subject, "formula_key": key,
                    "seed": job_seed(args, subject, round_index, index + 1),
                    "candidate_id": f"{subject}_{len(accepted) + 1:03d}",
                    "equation": final,
                    **publish_candidate(root, subject, len(accepted) + 1, run_dir, result, final),
                }
                _append_jsonl(accepted_path, entry)
                accepted.append(entry)
                known.add(key)
                publish_index(root)
            _append_jsonl(ledger, {"job_id": job_id, "status": status, "formula_key": key, "run_dir": str(run_dir)})
            terminal.add(job_id)
            print(f"{subject}: {len(accepted)}/{args.target_per_subject} candidates ({status})", flush=True)

        workers = getattr(args, "workers", 1)
        pending, errors = {}, []
        remaining = iter(jobs)
        exhausted = False
        submitted = 0
        progress_started = time.monotonic()
        progress_interval = getattr(args, "progress_interval", 30.0)
        pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="lineage")
        _print_progress(subject, round_index, len(accepted), args.target_per_subject,
                        [], progress_started, queued=len(jobs))
        try:
            while True:
                # Reserve one remaining target slot per in-flight job. Do not
                # speculatively spend model calls beyond the requested count.
                while (not errors and not exhausted and len(pending) < workers
                       and len(accepted) + len(pending) < args.target_per_subject):
                    job = next(remaining, None)
                    if job is None:
                        exhausted = True
                        break
                    pending[pool.submit(execute, job)] = job
                    submitted += 1
                if not pending:
                    break
                done, _ = wait(pending, timeout=progress_interval, return_when=FIRST_COMPLETED)
                if not done:
                    _print_progress(
                        subject,
                        round_index,
                        len(accepted),
                        args.target_per_subject,
                        list(pending.values()),
                        progress_started,
                        queued=max(0, len(jobs) - submitted),
                    )
                for future in sorted(done, key=lambda item: pending[item][0]):
                    job = pending.pop(future)
                    try:
                        try:
                            outcome = future.result()
                        except JobTimeoutError as exc:
                            if getattr(args, "on_request_error", "defer") != "defer":
                                raise
                            defer(job, str(exc))
                        else:
                            collect(job, outcome)
                    except Exception as exc:
                        errors.append(f"{exc} (log: {job[4]})")
                        print(f"Worker failed: {errors[-1]}. No new jobs will start; "
                              f"collecting {len(pending)} already running jobs.", file=sys.stderr, flush=True)
        except BaseException:
            cancelled.set()
            for future in pending:
                future.cancel()
            raise
        finally:
            pool.shutdown(wait=True, cancel_futures=True)
        if errors:
            raise RuntimeError("Parallel generation stopped; completed results are saved.\n" + "\n".join(errors))
    if len(accepted) < args.target_per_subject:
        raise RuntimeError(f"{subject}: only {len(accepted)}/{args.target_per_subject} candidates after "
                           f"{args.max_rounds} rounds. Inspect {ledger}; the requested count was NOT reached.")
    publish_index(root)
    print(f"Complete: {subject}, {len(accepted)} candidates -> {accepted_path}", flush=True)


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(prog="srbench generate", description=__doc__)
    parser.add_argument("--run-name", required=True)
    parser.add_argument("--subjects", choices=SUBJECTS, nargs="+", default=list(SUBJECTS))
    parser.add_argument("--only-subjects", choices=SUBJECTS, nargs="+",
                        help="Resume only these subjects; preserve the full subject set in batch_config.json")
    parser.add_argument("--target-per-subject", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=30, help="Maximum new gen0s per subject per round")
    parser.add_argument("--workers", type=int, default=1, help="Maximum concurrent lineages; independent of batch-size")
    parser.add_argument("--executor", choices=["local", "daytona"], default="local",
                        help="Run each lineage in a local subprocess or a separate Daytona sandbox")
    parser.add_argument("--daytona-snapshot", help="Optional Daytona Python snapshot with dependencies preinstalled")
    parser.add_argument("--job-timeout", type=int, default=14400, help="Seconds per lineage job, including remote setup")
    parser.add_argument("--progress-interval", type=float, default=30.0,
                        help="Seconds between scheduler heartbeat lines while workers are active")
    parser.add_argument("--on-request-error", choices=["stop", "defer"], default="defer",
                        help="Defer transient request failures and job timeouts; other errors still stop")
    parser.add_argument("--max-consecutive-request-errors", type=int, default=3,
                        help="Stop new jobs after this many consecutive transient failures")
    parser.add_argument("--n-subfields", type=int, default=7)
    parser.add_argument("--max-rounds", type=int, default=10, help="Finite budget; stop with an error if target remains unmet")
    parser.add_argument("--seed", type=int, default=20260916)
    parser.add_argument("--steps", type=int, default=5)
    parser.add_argument("--max-steps", type=int, default=15)
    parser.add_argument("--max-lineage-attempts", type=int, default=2)
    parser.add_argument("--max-static-input-dim", type=int, default=4)
    parser.add_argument("--max-ode-state-dim", type=int, default=4)
    parser.add_argument("--n-total", type=int, default=5000)
    parser.add_argument("--provider", choices=["anthropic", "openrouter", "openai"], default="anthropic")
    parser.add_argument("--model", default="claude-opus-4-7")
    parser.add_argument("--spec-model")
    parser.add_argument("--novelty-model")
    parser.add_argument("--base-url")
    parser.add_argument("--auth-source", choices=["auto", "api_key", "auth_token"], default="auto")
    parser.add_argument("--cli-path")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs"))
    parser.add_argument("--reuse-from", type=Path, default=None,
                        help="Reuse prior _checkpoints/*/round_*/gen0 equations and rerun only evolution")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if not args.run_name or Path(args.run_name).name != args.run_name or args.run_name in {".", ".."}:
        parser.error("run-name must be a single non-empty directory name")
    if len(set(args.subjects)) != len(args.subjects):
        parser.error("subjects must not repeat")
    args.only_subjects = args.only_subjects or list(args.subjects)
    if not set(args.only_subjects).issubset(args.subjects) or len(set(args.only_subjects)) != len(args.only_subjects):
        parser.error("only-subjects must be a nonempty subset of subjects without repeats")
    if not (1 <= args.n_subfields <= 7 and args.batch_size >= args.n_subfields and args.max_rounds >= 1
            and args.target_per_subject >= 1 and 1 <= args.steps <= args.max_steps
            and 1 <= args.max_lineage_attempts < 64 and args.n_total >= 1
            and args.max_static_input_dim >= 1 and args.max_ode_state_dim >= 1):
        parser.error("invalid counts, dimension limits or step budget")
    if (args.workers < 1 or args.job_timeout < 1 or args.progress_interval <= 0
            or args.max_consecutive_request_errors < 1):
        parser.error("workers, job-timeout, progress-interval and max-consecutive-request-errors must be positive")
    if args.executor == "daytona" and (args.provider == "anthropic" or args.cli_path):
        parser.error("Daytona generation currently supports openai/openrouter without a local cli-path")
    if args.seed < 0 or job_seed(args, "physics", args.max_rounds - 1, args.batch_size) + 63 >= 2**32:
        parser.error("seed allocation must fit unsigned 32-bit seeds")
    root = args.output_dir.resolve() / args.run_name
    config = {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()
              if key not in {"resume", "dry_run", "output_dir", "only_subjects", "workers", "executor", "daytona_snapshot", "job_timeout", "progress_interval",
                             "on_request_error", "max_consecutive_request_errors"}}
    execution = {key: getattr(args, key) for key in ("only_subjects", "workers", "executor", "daytona_snapshot", "job_timeout", "progress_interval",
                                                   "on_request_error", "max_consecutive_request_errors")}
    if args.dry_run:
        count = max(args.n_subfields, min(args.batch_size, args.target_per_subject))
        if args.reuse_from is not None:
            first_round_commands = [{
                "action": "reuse_equations",
                "subject": subject,
                "source_root": str(args.reuse_from),
                "source_round": "matching round, or last available source round",
            } for subject in args.only_subjects]
        else:
            first_round_commands = [generation_command(args, subject, 0, root / "_checkpoints" / subject / "round_001", count)
                                    for subject in args.only_subjects]
        print(json.dumps({"config": config, "execution": execution, "output": str(root),
                          "first_round_commands": first_round_commands,
                          "maximum_gen0_per_subject": args.max_rounds * args.batch_size,
                          "success_requires": "target_per_subject accepted, textually distinct candidates; no R2 screening"},
                         ensure_ascii=False, indent=2))
        return
    if root.exists() and not args.resume:
        parser.error(f"Run directory exists; use the same command with --resume: {root}")
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".scheduler.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("Another scheduler owns this run directory")
        config_path = root / "batch_config.json"
        if config_path.exists():
            saved_config = json.loads(config_path.read_text(encoding="utf-8"))
            # Runs created before ``reuse_from`` was added have no key.  Treat
            # that legacy representation as equivalent to the current null
            # default so a normal --resume can continue those checkpoints.
            if "reuse_from" not in saved_config and config.get("reuse_from") is None:
                saved_config["reuse_from"] = None
            if saved_config != config:
                parser.error("Resume requires the original run configuration (model, seed, subjects and budgets)")
        else:
            _write_json(config_path, config)
        if args.executor == "daytona":
            from srbench.generation.executors import check_daytona
            check_daytona(args.provider)
        _write_json(root / "execution.json", execution)
        _write_json(root / "run.json", {"version": 7, "status": "generating", "config": config})
        try:
            for subject in args.only_subjects:
                collect_subject(args, subject, root)
        except BaseException:
            publish_index(root)
            _write_json(root / "run.json", {"version": 7, "status": "incomplete", "config": config,
                "counts": candidate_counts(root)})
            raise
        counts = candidate_counts(root)
        complete = all(counts.get(subject, 0) >= args.target_per_subject for subject in args.subjects)
        _write_json(root / "run.json", {"version": 7, "status": "generated" if complete else "incomplete",
            "config": config, "counts": counts, "selected_subjects": args.only_subjects,
            "solver_evaluated": False})


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
