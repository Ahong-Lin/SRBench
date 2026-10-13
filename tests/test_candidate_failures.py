"""Bad numeric candidates should not stop unrelated scenarios or be retried on resume."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import numpy as np

from srbench.common.io import read_json, read_jsonl, append_jsonl
from srbench.generation import batch, data_generator, pipeline
from srbench.generation.checkpoints import candidate_failure
from srbench.generation.data_generator import CandidateDataError
from test_candidate_batch import options, write_candidate
from test_freedom_evolution import static_parent
from test_parallel_generation import prepare_round


LEGACY_NUMERIC_ERROR = "ValueError: candidate data has wrong row count or nonfinite values"


def record_failure(output, *, legacy=False, error=None):
    record = {"attempt": 1, "status": "pipeline_error" if legacy else "candidate_error",
              "error": error or (LEGACY_NUMERIC_ERROR if legacy else "CandidateDataError: 199 nonfinite rows"),
              "retryable": False}
    append_jsonl(output / "candidate_test/lineage_attempts.jsonl", record)
    return record


class CandidateFailureTests(unittest.TestCase):
    def test_invalid_evolution_retries_lineage_then_skips_seed(self):
        parent = static_parent() | {"scenario_id": "demo", "discipline": "science"}
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(io.StringIO()):
            root = Path(tmp)
            source = root / "input.jsonl"
            source.write_text(json.dumps(parent) + "\n")
            argv = ["--input", str(source), "--id", "demo", "--output-dir", str(root / "output"),
                    "--steps", "1", "--max-steps", "1", "--max-lineage-attempts", "2"]
            with patch.object(pipeline, "build_model_caller", return_value=Mock()), \
                    patch.object(pipeline, "_lineage", side_effect=pipeline.evolve.EvolvedEquationValidationError(
                        "mechanism does not match the plan")) as evolving, \
                    self.assertRaisesRegex(SystemExit, "No acceptable candidate after 2 lineages"):
                pipeline.main(argv)
            self.assertEqual(evolving.call_count, 2)
            run = next((root / "output").glob("candidate_*"))
            self.assertEqual([row["status"] for row in read_jsonl(run / "lineage_attempts.jsonl")],
                             ["reject_invalid_evolution"] * 2)
            self.assertTrue(batch.expected_rejection(root / "output"))
            with patch.object(pipeline, "build_model_caller", return_value=Mock()), \
                    patch.object(pipeline, "_lineage", side_effect=AssertionError("rejected lineages must not rerun")), \
                    self.assertRaisesRegex(SystemExit, "No acceptable candidate after 2 lineages"):
                pipeline.main(argv + ["--resume"])

    def test_nonfinite_data_ends_scenario_and_direct_resume_makes_no_model_calls(self):
        parent = static_parent() | {"scenario_id": "demo", "discipline": "science"}
        child = parent | {"expression": "acos(x)"}
        lineage = [pipeline.evolve._record(parent, "demo", 0, "base", ""),
                   pipeline.evolve._record(child, "demo", 1, "change_assumption", "")]
        spec = {"equation_type": "explicit", "integrator": "evaluate_explicit", "dependent_variable": "y",
                "independent_variables": [{"symbol": "x", "range": [2, 3], "n_points": 8}],
                "parameters": [], "rhs_for_integrator": "acos(x)", "noise": 0}
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(io.StringIO()), np.errstate(invalid="ignore"):
            root = Path(tmp)
            source = root / "input.jsonl"
            source.write_text(json.dumps(parent) + "\n")
            argv = ["--input", str(source), "--id", "demo", "--output-dir", str(root / "output"),
                    "--steps", "1", "--max-steps", "1", "--max-lineage-attempts", "4", "--n-total", "8"]
            with patch.object(pipeline, "build_model_caller", return_value=Mock()), \
                    patch.object(pipeline, "_lineage", return_value=(lineage, {"answer": "Yes"})) as evolving, \
                    patch.object(pipeline, "_plan_spec", return_value=spec), \
                    self.assertRaisesRegex(SystemExit, "skip this scenario"):
                pipeline.main(argv)
            self.assertEqual(evolving.call_count, 1)
            run = next((root / "output").glob("candidate_*"))
            failure = read_json(run / "lineage_attempt_01/failure.json")
            self.assertEqual(failure["status"], "candidate_error")
            self.assertEqual(failure["data_check"]["nonfinite_rows"], 8)
            self.assertEqual(failure["data_check"]["actual_rows"], 8)
            self.assertTrue(Path(failure["data_check"]["data_csv"]).exists())
            self.assertFalse((run / "lineage_attempt_02").exists())
            self.assertFalse((run / "final_result.json").exists())
            self.assertEqual(read_json(run / "lineage_attempt_01/progress.json")["stage"], "candidate_failed")
            with patch.object(pipeline, "build_model_caller", side_effect=AssertionError("must not call model")), \
                    patch.object(pipeline, "_generate", side_effect=AssertionError("must not regenerate bad data")), \
                    self.assertRaisesRegex(SystemExit, "previously failed numerically"):
                pipeline.main(argv + ["--resume"])
            self.assertEqual(len(read_jsonl(run / "lineage_attempts.jsonl")), 1)

    def test_numerical_arithmetic_errors_are_candidate_failures_but_runtime_bugs_are_not(self):
        for exc in (FloatingPointError("diverged"), OverflowError("overflow"), ZeroDivisionError("zero"),
                    RuntimeError("implementation bug")):
            expected = RuntimeError if isinstance(exc, RuntimeError) else CandidateDataError
            with self.subTest(error=type(exc).__name__), patch.object(pipeline, "generate", side_effect=exc), \
                    self.assertRaises(expected):
                pipeline._generate({}, "demo", 1, Path("unused"), 1, 8)

    def test_solver_failure_is_a_numeric_candidate_error(self):
        spec = {"independent_variables": [{"symbol": "t", "range": [0, 2], "n_points": 8}],
                "dependent_variable": "y", "rhs_for_integrator": "y**2", "initial_conditions": {"y": 1},
                "state_variables": ["y"], "state_rhs": ["y**2"], "parameters": []}
        for generator in (data_generator.gen_integrate_ode, data_generator.gen_integrate_system):
            with self.subTest(generator=generator.__name__), \
                    patch("scipy.integrate.solve_ivp", return_value=SimpleNamespace(success=False, message="step size too small")), \
                    self.assertRaisesRegex(CandidateDataError, "integration failed"):
                generator(spec, seed=1)

    def test_legacy_recognition_is_exact_and_latest_outcome_takes_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            run = output / "candidate_test"
            record_failure(output, legacy=True)
            self.assertEqual(candidate_failure(run)["legacy_status"], "pipeline_error")
            append_jsonl(run / "lineage_attempts.jsonl", {"attempt": 1, "status": "candidate_generated"})
            self.assertIsNone(candidate_failure(run))
            record_failure(output, legacy=True, error="ValueError: unexpected shape in model implementation")
            self.assertIsNone(candidate_failure(run))


class ScenarioSkippingTests(unittest.TestCase):
    def test_new_numeric_failure_moves_to_next_scenario_and_is_terminal_on_resume(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            root = Path(tmp)
            rnd, _ = prepare_round(root, 3)
            calls = []

            def run(command, log, **kwargs):
                item = command[command.index("--id") + 1]
                calls.append(item)
                output = Path(command[command.index("--output-dir") + 1])
                if item == "item_0":
                    record_failure(output)
                    return 1
                write_candidate(output, "a*x+" + item[-1])
                return 0

            with patch.object(batch, "_run", side_effect=run):
                batch.collect_subject(options(target_per_subject=1), "biology", root)
                self.assertEqual(calls, ["item_0", "item_1"])
                batch.collect_subject(options(target_per_subject=2, resume=True), "biology", root)
            self.assertEqual(calls, ["item_0", "item_1", "item_2"])
            rows = read_jsonl(root / "_checkpoints/biology/attempts.jsonl")
            self.assertEqual([row["status"] for row in rows], ["skipped", "accepted", "accepted"])
            self.assertEqual(rows[0]["reason"], "invalid_numeric_data")
            self.assertEqual(batch.candidate_counts(root)["biology"], 2)
            self.assertTrue((rnd / "evolved/job_001/candidate_test/lineage_attempts.jsonl").exists())

    def test_legacy_failure_skips_worker_and_continues_to_next_scenario(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            root = Path(tmp)
            rnd, _ = prepare_round(root, 2)
            record_failure(rnd / "evolved/job_001", legacy=True)

            def run(command, log, **kwargs):
                self.assertEqual(command[command.index("--id") + 1], "item_1")
                write_candidate(Path(command[command.index("--output-dir") + 1]), "a*x+1")
                return 0

            with patch.object(batch, "_run", side_effect=run) as worker:
                batch.collect_subject(options(target_per_subject=1, resume=True), "biology", root)
            self.assertEqual(worker.call_count, 1)
            self.assertEqual([row["status"] for row in read_jsonl(root / "_checkpoints/biology/attempts.jsonl")], ["skipped", "accepted"])

    def test_skipped_candidates_do_not_count_as_success_or_trip_service_failure_limit(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            root = Path(tmp)
            rnd, _ = prepare_round(root, 4)
            for index in range(4):
                record_failure(rnd / f"evolved/job_{index + 1:03d}")
            with patch.object(batch, "_run", side_effect=AssertionError("saved numeric failures must not rerun")), \
                    self.assertRaisesRegex(RuntimeError, "only 0/1 candidates.*requested count was NOT reached"):
                batch.collect_subject(options(batch_size=4, target_per_subject=1, max_rounds=1), "biology", root)
            self.assertEqual([row["status"] for row in read_jsonl(root / "_checkpoints/biology/attempts.jsonl")], ["skipped"] * 4)

    def test_parallel_numeric_failure_keeps_other_worker_and_starts_replacement(self):
        # Exercise the concurrent coordinator with mocked workers.
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            root = Path(tmp)
            prepare_round(root, 3)
            calls = []

            def run(command, log, **kwargs):
                item = command[command.index("--id") + 1]
                calls.append(item)
                output = Path(command[command.index("--output-dir") + 1])
                if item == "item_0":
                    record_failure(output)
                    return 1
                write_candidate(output, "a*x+" + item[-1])
                return 0

            with patch.object(batch, "_run", side_effect=run):
                batch.collect_subject(options(target_per_subject=2, workers=2), "biology", root)
            self.assertEqual(set(calls), {"item_0", "item_1", "item_2"})
            self.assertEqual(batch.candidate_counts(root)["biology"], 2)
            self.assertEqual(len(read_jsonl(root / "_checkpoints/biology/attempts.jsonl")), 3)


if __name__ == "__main__":
    unittest.main()
