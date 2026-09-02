#!/usr/bin/env python3
"""Run the fixed core-taxonomy SRBench v6 experiment, resumably.

The plan is intentionally narrow and explicit:

* biology, chemistry, physics, materials, economy: 7 frozen subfields x 10 scenarios;
* AI: its one frozen ``scaling_laws`` subfield x 10 *generated* scenarios;
* every successfully generated gen0 equation is sent to the same existing
  ``evolution_pipeline.py`` workflow.

This script orchestrates existing entry points.  It does not decide novelty,
data quality, R², or whether a task is difficult: those decisions remain inside
``evolution_pipeline.py`` and its configured Harbor solver command.

The batch ledger is append-only JSONL.  A resumed run skips a subject once its
generation stage is complete and skips equation IDs which already have a
terminal evolution record.  Use a stable --run-name when resuming.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PLAN: tuple[tuple[str, int, str], ...] = (
    ("biology", 7, "auto"),
    ("chemistry", 7, "auto"),
    ("physics", 7, "auto"),
    ("materials", 7, "auto"),
    ("economy", 7, "auto"),
    # The frozen AI taxonomy has one subfield but its reviewed seed file has
    # only seven records.  ``generate`` intentionally creates ten new gen0
    # scenarios under that same frozen scaling_laws subfield; it never repeats
    # seed records merely to reach ten.
    ("AI", 1, "generate"),
)
SCENARIOS_PER_SUBFIELD = 10


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, value: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSONL at {path}:{number}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"Non-object JSONL item at {path}:{number}")
        records.append(value)
    return records


def _terminal_equation_ids(records: list[dict[str, Any]]) -> set[tuple[str, str]]:
    # Infrastructure failures are deliberately *not* terminal: after repairing
    # credentials, Harbor, or a provider outage, --resume should retry them.
    terminal = {"accepted", "rejected", "skipped_existing"}
    return {
        (str(record["subject"]), str(record["equation_id"]))
        for record in records
        if record.get("stage") == "evolution" and record.get("status") in terminal
        and record.get("subject") is not None and record.get("equation_id") is not None
    }


def _run(command: list[str], *, cwd: Path, log_path: Path) -> subprocess.CompletedProcess[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    log_path.write_text(
        "$ " + " ".join(command) + "\n\n[stdout]\n" + result.stdout
        + "\n[stderr]\n" + result.stderr + "\n",
        encoding="utf-8",
    )
    return result


def _generated_equations(batch_dir: Path, subject: str) -> Path:
    return batch_dir / "gen0" / "Equations" / subject / "equations.jsonl"


def _subject_complete(records: list[dict[str, Any]], subject: str) -> bool:
    return any(record.get("stage") == "generation" and record.get("subject") == subject
               and record.get("status") == "complete" for record in records)


def _evolution_status(result: subprocess.CompletedProcess[str]) -> str:
    """Separate an exhausted difficulty gate from an infrastructure failure."""
    if result.returncode == 0:
        return "accepted"
    transcript = result.stdout + "\n" + result.stderr
    if "No acceptable final task after" in transcript:
        return "rejected"
    return "execution_failure"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the 360-scenario core-taxonomy SRBench v6 batch.")
    parser.add_argument("--run-name", required=True,
                        help="Stable batch name under outputs/Core_Taxonomy; reuse with --resume.")
    parser.add_argument("--mode", choices=["candidate", "difficulty_gate"], default="candidate")
    parser.add_argument("--provider", choices=["anthropic", "openrouter"], default="anthropic")
    parser.add_argument("--model", default="claude-opus-4-7",
                        help="Model used for scenario, equation, evolution, novelty, and DataSpec stages.")
    parser.add_argument("--equation-model", default=None)
    parser.add_argument("--spec-model", default=None)
    parser.add_argument("--novelty-model", default=None)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--auth-source", choices=["auto", "api_key", "auth_token"], default="auto")
    parser.add_argument("--cli-path", default=None)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--operation-policy", choices=["guided", "random"], default="guided")
    parser.add_argument("--embedding-policy", choices=["random"], default="random")
    parser.add_argument("--steps", type=int, default=5)
    parser.add_argument("--max-steps", type=int, default=None)
    parser.add_argument("--max-lineage-attempts", type=int, default=1,
                        help="Per-gen0 evolution budget; the full-taxonomy default is one lineage.")
    parser.add_argument("--n-total", type=int, default=5000)
    parser.add_argument("--test-points", type=int, default=500)
    parser.add_argument("--easy-r2", type=float, default=0.90)
    parser.add_argument("--difficulty-policy", choices=["one_shot", "replan_once"], default="one_shot",
                        help="High-R² policy; one_shot directly rejects this gen0 and proceeds to the next one.")
    parser.add_argument("--harbor-template", type=Path, default=Path("Harbor_example"))
    parser.add_argument("--solver-command", default=None,
                        help="Required for difficulty_gate; template accepts {task}, {train}, {test}, {spec}, {output}.")
    parser.add_argument("--continue-on-error", action="store_true",
                        help="Continue after unexpected generation/execution failures. By default those failures stop the batch; expected scientific rejections always continue.")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.mode == "difficulty_gate" and not args.solver_command:
        raise SystemExit("--mode difficulty_gate requires --solver-command")
    if args.resume is False and args.run_name.strip() == "":
        raise SystemExit("--run-name cannot be empty")

    repo = Path(__file__).resolve().parents[1]
    batch_dir = repo / "outputs" / "Core_Taxonomy" / args.run_name
    ledger = batch_dir / "batch_ledger.jsonl"
    config_path = batch_dir / "batch_config.json"
    if batch_dir.exists() and not args.resume:
        raise SystemExit(f"Batch directory exists; pass --resume or choose a new --run-name: {batch_dir}")
    batch_dir.mkdir(parents=True, exist_ok=True)
    old_records = _read_jsonl(ledger)
    if config_path.exists():
        saved = json.loads(config_path.read_text(encoding="utf-8"))
        if saved.get("mode") != args.mode:
            raise SystemExit("Cannot resume a batch with a different --mode")
    else:
        _write_json(config_path, {
            "schema_version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "mode": args.mode,
            "operation_policy": args.operation_policy,
            "embedding_policy": args.embedding_policy,
            "max_lineage_attempts": args.max_lineage_attempts,
            "difficulty_policy": args.difficulty_policy if args.mode == "difficulty_gate" else None,
            "scenarios_per_subfield": SCENARIOS_PER_SUBFIELD,
            "plan": [
                {"subject": subject, "n_subfields": n, "equation_mode": equation_mode,
                 "n_scenarios": n * SCENARIOS_PER_SUBFIELD}
                for subject, n, equation_mode in PLAN
            ],
            "total_scenarios": sum(n * SCENARIOS_PER_SUBFIELD for _, n, _ in PLAN),
            "notes": {
                "AI": "Generate ten new gen0 scaling-law scenarios; do not duplicate the seven fixed seed equations.",
                "difficulty_gate": "The existing pipeline creates independent train/hidden CSVs from one DataSpec and scores the Harbor solver on hidden R². The batch default is one_shot: R² > 0.90 directly rejects that gen0.",
            },
        })

    if args.dry_run:
        print(json.dumps(json.loads(config_path.read_text(encoding="utf-8")), ensure_ascii=False, indent=2))
        return

    records = old_records
    for subject_index, (subject, n_subfields, equation_mode) in enumerate(PLAN):
        equations_path = _generated_equations(batch_dir, subject)
        if not _subject_complete(records, subject):
            command = [sys.executable, "auto_workflow.py", "--subject", subject,
                       "--scenarios", str(n_subfields * SCENARIOS_PER_SUBFIELD),
                       "--n-subfields", str(n_subfields), "--subfield-source", "fixed",
                       "--equation-mode", equation_mode,
                       "--provider", args.provider, "--model", args.model,
                       "--seed", str(args.seed + subject_index), "--batch-size", "10",
                       "--output-dir", str(batch_dir / "gen0"), "--run-name", subject]
            if args.equation_model:
                command += ["--equation-model", args.equation_model]
            if args.base_url:
                command += ["--base-url", args.base_url]
            if args.auth_source:
                command += ["--auth-source", args.auth_source]
            if args.resume:
                command.append("--resume")
            result = _run(command, cwd=repo, log_path=batch_dir / "logs" / f"generate_{subject}.log")
            status = "complete" if result.returncode == 0 else "generation_error"
            entry = {"stage": "generation", "subject": subject, "status": status,
                     "returncode": result.returncode, "equations": str(equations_path),
                     "log": str(batch_dir / "logs" / f"generate_{subject}.log")}
            _append_jsonl(ledger, entry)
            records.append(entry)
            if result.returncode != 0 and not args.continue_on_error:
                raise SystemExit(f"Generation failed for {subject}; inspect {entry['log']}")

        if not equations_path.exists():
            if args.continue_on_error:
                continue
            raise SystemExit(f"No equations file for {subject}: {equations_path}")
        try:
            equations = _read_jsonl(equations_path)
        except Exception as exc:
            if not args.continue_on_error:
                raise
            entry = {"stage": "generation", "subject": subject, "status": "generation_error",
                     "error": f"{type(exc).__name__}: {exc}", "equations": str(equations_path)}
            _append_jsonl(ledger, entry)
            records.append(entry)
            continue

        done = _terminal_equation_ids(records)
        for equation_index, equation in enumerate(equations):
            equation_id = str(equation.get("scenario_id") or equation.get("id") or "")
            if not equation_id:
                entry = {"stage": "evolution", "subject": subject, "status": "generation_error",
                         "error": "missing scenario_id", "equation_index": equation_index}
                _append_jsonl(ledger, entry)
                records.append(entry)
                continue
            if (subject, equation_id) in done:
                continue
            output_dir = batch_dir / "evolved" / subject / equation_id
            command = [sys.executable, "evolution_pipeline.py", "--input", str(equations_path),
                       "--id", equation_id, "--discipline", subject, "--mode", args.mode,
                       "--steps", str(args.steps), "--max-lineage-attempts", str(args.max_lineage_attempts),
                       "--n-total", str(args.n_total), "--seed", str(args.seed + 1000 * subject_index + equation_index),
                       "--operation-policy", args.operation_policy,
                       "--embedding-policy", args.embedding_policy,
                       "--provider", args.provider, "--model", args.model, "--output-dir", str(output_dir)]
            if args.max_steps is not None:
                command += ["--max-steps", str(args.max_steps)]
            if args.spec_model:
                command += ["--spec-model", args.spec_model]
            if args.novelty_model:
                command += ["--novelty-model", args.novelty_model]
            if args.base_url:
                command += ["--base-url", args.base_url]
            if args.auth_source:
                command += ["--auth-source", args.auth_source]
            if args.cli_path:
                command += ["--cli-path", args.cli_path]
            if args.mode == "difficulty_gate":
                command += ["--test-points", str(args.test_points), "--easy-r2", str(args.easy_r2),
                            "--difficulty-policy", args.difficulty_policy,
                            "--harbor-template", str(args.harbor_template),
                            "--solver-command", args.solver_command]
            result = _run(command, cwd=repo,
                          log_path=batch_dir / "logs" / "evolve" / subject / f"{equation_id}.log")
            status = _evolution_status(result)
            entry = {"stage": "evolution", "subject": subject, "equation_id": equation_id,
                     "status": status, "returncode": result.returncode,
                     "output_dir": str(output_dir),
                     "log": str(batch_dir / "logs" / "evolve" / subject / f"{equation_id}.log")}
            _append_jsonl(ledger, entry)
            records.append(entry)
            # A nonzero evolution exit can be an expected one-shot rejection
            # (all internal gates exhausted).  Continue to the next gen0 in
            # that case.  Stop immediately on real infrastructure or runtime
            # failures unless the operator explicitly opts into continuation.
            if status == "execution_failure" and not args.continue_on_error:
                raise SystemExit(f"Evolution failed for {subject}/{equation_id}; inspect {entry['log']}")

    print(f"Batch complete. Ledger: {ledger}")


if __name__ == "__main__":
    main()
