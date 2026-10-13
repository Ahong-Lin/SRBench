"""Offline interruption/recovery tests: model and network calls are mocked."""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import httpx

from srbench.common.io import read_json, read_jsonl, write_json
from srbench.common.model_provider import ModelCaller, ModelServiceError
from srbench.generation import batch, data_spec, evolution, novelty, pipeline, scenarios
from srbench.generation.executors import JobTimeoutError
from test_candidate_batch import options, write_candidate
from test_freedom_evolution import static_parent, child_with_freedom, plan_for, data_spec as spec_for
from test_parallel_generation import prepare_round


def lineage_args(**changes):
    return SimpleNamespace(**(dict(max_steps=3, steps=3, operation_policy="guided", discipline="science",
        model="offline", novelty_model=None, assumption_mode="extended", p_assumption=0.5,
        max_static_input_dim=4, max_ode_state_dim=4, resume=False) | changes))


class RequestBudgetTests(unittest.TestCase):
    def test_timeout_budget_is_not_multiplied_by_generation_correction_loops(self):
        caller = ModelCaller("openai", openai_api_key="test-key", openai_base_url="https://api.invalid/v1")
        parent = static_parent()
        operations = {
            "plan": lambda: evolution.plan_evolution_step(caller, parent, "science", "scenario", "offline", str.strip),
            "equation": lambda: evolution.evolve_once(caller, parent, "change_assumption", "science", "scenario",
                                                      "offline", str.strip, "extended", 4, 4),
            "novelty": lambda: novelty.check_novelty(caller, parent, "science", "scenario", "offline"),
            "scenarios": lambda: scenarios.expand_discipline(caller, "science", 3, "offline"),
            "dataspec": lambda: data_spec.plan_data_generation(parent, "science", provider="openai", model="offline"),
        }
        for name, run in operations.items():
            with self.subTest(stage=name), patch.dict(os.environ, {
                    "SRBENCH_OPENAI_MAX_RETRIES": "1", "SRBENCH_OPENAI_READ_TIMEOUT": "17"}), \
                    patch("srbench.common.model_provider.time.sleep"), \
                    patch.object(data_spec, "build_model_caller", return_value=caller), \
                    patch("srbench.common.model_provider.httpx.post", side_effect=httpx.ReadTimeout("offline")) as post, \
                    contextlib.redirect_stderr(io.StringIO()), self.assertRaises(ModelServiceError) as caught:
                run()
            self.assertTrue(caught.exception.retryable)
            self.assertEqual(post.call_count, 2)
            self.assertEqual(post.call_args.kwargs["timeout"].read, 17)

    def test_authentication_errors_are_not_retried_by_the_plan_loop(self):
        caller = ModelCaller("openai", openai_api_key="test-key", openai_base_url="https://api.invalid/v1")
        with patch("srbench.common.model_provider.httpx.post", return_value=httpx.Response(401, json={"error": "bad key"})) as post, \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(ModelServiceError) as caught:
            evolution.plan_evolution_step(caller, static_parent(), "science", "scenario", "offline", str.strip)
        self.assertFalse(caught.exception.retryable)
        self.assertEqual(post.call_count, 1)


class LineageRecoveryTests(unittest.TestCase):
    def test_resume_preserves_completed_equations_pending_selection_and_rng(self):
        parent = static_parent()
        children = [child_with_freedom(parent, "add_input") for _ in range(3)]
        for i, child in enumerate(children):
            child["expression"] += f" + {i}"
        plan = plan_for(children[0])
        # Both the new RNG snapshot and the old selection-only checkpoints work.
        for legacy in (False, True):
            for policy in ("guided", "random"):
                with self.subTest(legacy=legacy, policy=policy), tempfile.TemporaryDirectory() as tmp, \
                        contextlib.redirect_stderr(io.StringIO()):
                    root = Path(tmp)
                    args = lineage_args(operation_policy=policy)
                    continuous_rng, resumed_rng = random.Random(7), random.Random(7)
                    with patch.object(evolution, "plan_evolution_step", return_value=plan), \
                            patch.object(evolution, "evolve_once", side_effect=copy.deepcopy(children)), \
                            patch.object(novelty, "check_novelty", return_value={"answer": "Yes"}):
                        expected, _ = pipeline._lineage(parent, "demo", Mock(), args, continuous_rng, None, root / "continuous")
                    with patch.object(evolution, "plan_evolution_step", return_value=plan), \
                            patch.object(evolution, "evolve_once", side_effect=[children[0], ModelServiceError("timeout", retryable=True)]), \
                            self.assertRaises(ModelServiceError):
                        pipeline._lineage(parent, "demo", Mock(), args, random.Random(7), None, root / "interrupted")
                    directory = root / "interrupted"
                    self.assertEqual(len(read_jsonl(directory / "lineage.jsonl")), 2)
                    if legacy:
                        for path in directory.glob("gen_*_selection.json"):
                            selection = read_json(path)
                            selection.pop("rng_state_after")
                            write_json(path, selection)
                    saved_selection = read_json(directory / "gen_002_selection.json")
                    args.resume = True
                    with patch.object(evolution, "plan_evolution_step", return_value=plan) as planning, \
                            patch.object(evolution, "evolve_once", side_effect=copy.deepcopy(children[1:])) as evolving, \
                            patch.object(novelty, "check_novelty", return_value={"answer": "Yes"}):
                        actual, _ = pipeline._lineage(parent, "demo", Mock(), args, resumed_rng, None, directory)
                    self.assertEqual(actual, expected)
                    self.assertEqual(evolving.call_count, 2)
                    self.assertEqual(planning.call_count, 1 if policy == "guided" else 0)
                    self.assertEqual(evolving.call_args_list[0].kwargs["embedding_pattern"], saved_selection["embedding"])
                    self.assertEqual(evolving.call_args_list[0].kwargs["evolution_plan"], saved_selection["plan"])
                    self.assertEqual(continuous_rng.getstate(), resumed_rng.getstate())
                    self.assertEqual(read_jsonl(directory / "lineage.jsonl"), expected)

    def test_novelty_is_never_called_after_requested_steps(self):
        parent = static_parent()
        child = child_with_freedom(parent, "add_input")
        args = lineage_args(steps=1)
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(io.StringIO()):
            directory = Path(tmp)
            with patch.object(evolution, "plan_evolution_step", return_value=plan_for(child)), \
                    patch.object(evolution, "evolve_once", return_value=child), \
                    patch.object(novelty, "check_novelty", side_effect=AssertionError("novelty disabled")) as judge:
                lineage, result = pipeline._lineage(parent, "demo", Mock(), args, random.Random(7), None, directory)
            judge.assert_not_called()
            self.assertEqual(result["answer"], "NOT_EVALUATED")
            self.assertEqual(len(lineage), 2)

    def test_cached_spec_recovers_finalization_without_duplicate_lineage_or_model_calls(self):
        parent = static_parent() | {"scenario_id": "demo", "discipline": "science"}
        child = child_with_freedom(parent, "add_input")
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(io.StringIO()), \
                patch.object(pipeline, "build_model_caller", return_value=Mock()):
            root = Path(tmp)
            source = root / "input.jsonl"
            source.write_text(json.dumps(parent) + "\n")
            argv = ["--input", str(source), "--id", "demo", "--output-dir", str(root / "output"),
                    "--steps", "1", "--max-steps", "1", "--max-lineage-attempts", "1", "--n-total", "32"]
            with patch.object(evolution, "plan_evolution_step", return_value=plan_for(child)), \
                    patch.object(evolution, "evolve_once", return_value=child), \
                    patch.object(novelty, "check_novelty", return_value={"answer": "Yes"}), \
                    patch.object(pipeline, "_plan_spec", return_value=spec_for(child).model_dump()), \
                    patch.object(pipeline, "_generate", side_effect=RuntimeError("numeric interruption")), \
                    self.assertRaisesRegex(RuntimeError, "numeric interruption"):
                pipeline.main(argv)
            with patch.object(evolution, "plan_evolution_step", side_effect=AssertionError("cached plan")), \
                    patch.object(evolution, "evolve_once", side_effect=AssertionError("cached equation")), \
                    patch.object(novelty, "check_novelty", side_effect=AssertionError("cached novelty")), \
                    patch.object(pipeline, "_plan_spec", side_effect=AssertionError("cached spec")):
                pipeline.main(argv + ["--resume"])
                run, _, result = batch.completed_candidate(root / "output")
                rows = read_jsonl(Path(result["candidate"]["spec"]).parent / "accepted_lineage.jsonl")
                self.assertEqual([item["generation"] for item in rows], [0, 1])
                self.assertEqual(result["candidate"]["n_points"], 32)
                self.assertEqual(len(list((root / "output").glob("candidate_*"))), 1)
                # A result marker is not sufficient if the referenced data is lost.
                Path(result["candidate"]["data_csv"]).unlink()
                pipeline.main(argv + ["--resume"])
                self.assertIsNotNone(batch.completed_candidate(root / "output"))
                with patch.object(pipeline, "_generate", side_effect=AssertionError("already complete")):
                    pipeline.main(argv + ["--resume"])
                with self.assertRaisesRegex(ValueError, "same lineage configuration"):
                    pipeline.main(argv + ["--resume", "--model", "changed-model"])
            self.assertEqual(read_json(run / "lineage_attempt_01/progress.json")["stage"], "complete")
            self.assertFalse((run / "lineage_attempt_01/failure.json").exists())
            saved_failures = list((run / "lineage_attempt_01").glob("failure_*.json"))
            self.assertEqual(len(saved_failures), 1)
            self.assertIn("numeric interruption", read_json(saved_failures[0])["error"])
            history = read_json(run / "lineage_attempt_01/mechanism_observation_history.json")
            self.assertEqual([row["generation"] for row in history], [1])
            self.assertEqual(read_json(run / "final_spec.json")["mechanism_observation_history"], history)


    def test_request_failure_is_recorded_with_retryability(self):
        for retryable in (True, False):
            with self.subTest(retryable=retryable), tempfile.TemporaryDirectory() as tmp, \
                    contextlib.redirect_stderr(io.StringIO()), patch.object(pipeline, "build_model_caller", return_value=Mock()), \
                    patch.object(pipeline, "_lineage", side_effect=ModelServiceError("offline", retryable=retryable)):
                root = Path(tmp)
                source = root / "input.jsonl"
                source.write_text(json.dumps(static_parent() | {"scenario_id": "demo"}) + "\n")
                with self.assertRaisesRegex(RuntimeError, "offline"):
                    pipeline.main(["--input", str(source), "--id", "demo", "--output-dir", str(root / "output")])
                failure = read_json(next((root / "output").glob("candidate_*/lineage_attempt_01/failure.json")))
                self.assertEqual(failure["status"], "request_error")
                self.assertEqual(failure["retryable"], retryable)
                self.assertEqual(batch.transient_failure(root / "output") is not None, retryable)


class SchedulerRecoveryTests(unittest.TestCase):
    def test_deferred_job_allows_next_job_and_remains_resumable(self):
        for timeout in (False, True):
            with self.subTest(timeout=timeout), tempfile.TemporaryDirectory() as tmp, \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                root = Path(tmp)
                prepare_round(root, 2)
                calls = []

                def failing(command, log, **kwargs):
                    item = command[command.index("--id") + 1]
                    calls.append(item)
                    output = Path(command[command.index("--output-dir") + 1])
                    if item == "item_0":
                        if timeout:
                            raise JobTimeoutError("job time limit")
                        batch._append_jsonl(output / "candidate_test/lineage_attempts.jsonl", {
                            "attempt": 1, "status": "request_error", "retryable": True, "error": "read timeout"})
                        return 1
                    write_candidate(output, "a*x+1")
                    return 0

                with patch.object(batch, "_run", side_effect=failing):
                    batch.collect_subject(options(target_per_subject=1), "biology", root)
                self.assertEqual(calls, ["item_0", "item_1"])
                ledger = root / "_checkpoints/biology/attempts.jsonl"
                self.assertEqual([row["status"] for row in read_jsonl(ledger)], ["deferred", "accepted"])

                def resumed(command, log, **kwargs):
                    self.assertEqual(command[command.index("--id") + 1], "item_0")
                    self.assertIn("--resume", command)
                    write_candidate(Path(command[command.index("--output-dir") + 1]), "a*x+2")
                    return 0

                with patch.object(batch, "_run", side_effect=resumed) as worker:
                    batch.collect_subject(options(target_per_subject=2, resume=True), "biology", root)
                self.assertEqual(worker.call_count, 1)
                self.assertEqual(batch.candidate_counts(root)["biology"], 2)

    def test_repeated_transient_failures_stop_new_requests(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            root = Path(tmp)
            prepare_round(root, 5)
            with patch.object(batch, "_run", side_effect=JobTimeoutError("time limit")) as worker, \
                    self.assertRaisesRegex(RuntimeError, "3 consecutive transient failures"):
                batch.collect_subject(options(batch_size=5, target_per_subject=5), "biology", root)
            self.assertEqual(worker.call_count, 3)
            self.assertEqual([row["status"] for row in read_jsonl(root / "_checkpoints/biology/attempts.jsonl")], ["deferred"] * 3)

    def test_auth_or_pipeline_errors_and_explicit_stop_policy_are_not_deferred(self):
        for status, retryable, policy in (("request_error", False, "defer"), ("pipeline_error", False, "defer"),
                                          ("request_error", True, "stop")):
            with self.subTest(status=status, retryable=retryable, policy=policy), tempfile.TemporaryDirectory() as tmp, \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                root = Path(tmp)
                prepare_round(root, 2)

                def failing(command, log, **kwargs):
                    output = Path(command[command.index("--output-dir") + 1])
                    batch._append_jsonl(output / "candidate_test/lineage_attempts.jsonl", {
                        "attempt": 1, "status": status, "retryable": retryable, "error": "offline"})
                    return 1

                with patch.object(batch, "_run", side_effect=failing) as worker, \
                        self.assertRaisesRegex(RuntimeError, "Evolution failed"):
                    batch.collect_subject(options(on_request_error=policy), "biology", root)
                self.assertEqual(worker.call_count, 1)
                self.assertFalse(read_jsonl(root / "_checkpoints/biology/attempts.jsonl"))

    def test_later_scientific_verdict_supersedes_earlier_failure_in_same_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "candidate_test/lineage_attempts.jsonl"
            batch._append_jsonl(path, {"attempt": 1, "status": "request_error", "retryable": True})
            self.assertFalse(batch.expected_rejection(root))
            batch._append_jsonl(path, {"attempt": 1, "status": "reject_not_novel"})
            self.assertTrue(batch.expected_rejection(root))
            self.assertIsNone(batch.transient_failure(root))


if __name__ == "__main__":
    unittest.main()
