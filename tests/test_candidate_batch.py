import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from srbench.generation import batch


def options(**overrides):
    values = dict(run_name="offline", subjects=["biology", "physics"], target_per_subject=2,
                  batch_size=3, n_subfields=1, max_rounds=3, seed=7, steps=5, max_steps=15,
                  max_lineage_attempts=4, max_static_input_dim=4, max_ode_state_dim=4,
                  n_total=5000, provider="anthropic", model="offline", auth_source="auto",
                  base_url=None, spec_model=None, novelty_model=None, cli_path=None)
    return SimpleNamespace(**(values | overrides))


def equation(expression="a*x"):
    return dict(model_family="static", equation_type="static_explicit", target_symbol="y",
                expression=expression, symbols=["y", "x", "a"], symbol_properties=["O", "V", "P"])


def write_candidate(output, expression):
    run = output / "candidate_test"
    attempt = run / "lineage_attempt_01"
    attempt.mkdir(parents=True)
    (attempt / "accepted_lineage.jsonl").write_text(json.dumps(equation(expression)) + "\n")
    (attempt / "candidate_spec.json").write_text("{}")
    (attempt / "data.csv").write_text("x,y\n1,1\n")
    (run / "final_spec.json").write_text("{}")
    batch._write_json(run / "final_result.json", {
        "status": "candidate_generated", "candidate": {
            "spec": str(attempt / "candidate_spec.json"), "data_csv": str(attempt / "data.csv"),
        },
    })


class CandidateBatchTests(unittest.TestCase):
    def test_republishing_old_candidate_exports_clean_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_candidate(root / "checkpoints", "a*x")
            run = root / "checkpoints/candidate_test"
            spec = {"dependent_variable": "y", "noise": 0.5, "excitation_ok": False}
            batch._write_json(run / "final_spec.json", spec)
            source = run / "lineage_attempt_01/data.csv"
            source.write_text("x,y,y_noisy\n1,2,9\n2,4,-5\n")
            result = json.loads((run / "final_result.json").read_text())
            batch.publish_candidate(root, "biology", 1, run, result, equation())
            published = root / "01_generated/biology_001"
            self.assertEqual(json.loads((published / "spec.json").read_text())["noise"], 0)
            self.assertEqual((published / "data.csv").read_text(), "x,y\n1,2\n2,4\n")
            self.assertIn("y_noisy", source.read_text())

    def test_published_archive_survives_checkpoint_removal(self):
        import shutil
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_candidate(root / "checkpoints", "a*x")
            run = root / "checkpoints/candidate_test"
            attempt = run / "lineage_attempt_01"
            traces = attempt / "model_calls"
            traces.mkdir()
            (traces / "gen_001_plan.jsonl").write_text('{"raw": "plan"}\n')
            (attempt / "gen_001_selection.json").write_text('{"operation": "add_term"}')
            failed = run / "lineage_attempt_02"
            failed.mkdir()
            (failed / "failure.json").write_text('{"error": "timeout"}')
            result = json.loads((run / "final_result.json").read_text())
            paths = batch.publish_candidate(root, "biology", 1, run, result, equation())
            shutil.rmtree(root / "checkpoints")
            archive = root / paths["lineage_archive"]
            self.assertIn('"plan"', (archive / "lineage_attempt_01/model_calls/gen_001_plan.jsonl").read_text())
            manifest = json.loads((archive / "archive_manifest.json").read_text())
            self.assertIn("lineage_attempt_02/failure.json", manifest["files"])
            self.assertTrue((archive / "lineage_attempt_01/accepted_lineage.jsonl").exists())

    def test_seeds_are_disjoint_across_subjects_rounds_jobs_and_attempts(self):
        args = options(batch_size=30, max_rounds=10)
        seeds = [batch.job_seed(args, subject, rnd, slot) + attempt
                 for subject in batch.SUBJECTS for rnd in range(args.max_rounds)
                 for slot in range(args.batch_size + 1) for attempt in range(args.max_lineage_attempts + 1)]
        self.assertEqual(len(seeds), len(set(seeds)))
        self.assertEqual(batch.job_seed(args, "physics", 1, 3),
                         batch.job_seed(options(batch_size=30, max_rounds=10, subjects=["physics"]), "physics", 1, 3))

    def test_duplicate_key_ignores_formatting_but_preserves_variable_roles_and_full_ode(self):
        original = equation()
        self.assertEqual(batch.formula_key(original), batch.formula_key(equation("a * (x)")))
        promoted = copy.deepcopy(original)
        promoted["symbol_properties"][-1] = "V"
        self.assertNotEqual(batch.formula_key(original), batch.formula_key(promoted))
        ode = equation() | {"model_family": "ode", "equation_type": "ode_system",
                            "ode_system": {"time_symbol": "t", "target_state": "x",
                                           "states": [{"symbol": "x", "rhs": "a*x", "initial_condition": 1}]}}
        other = copy.deepcopy(ode)
        other["ode_system"]["states"][0]["initial_condition"] = 2
        self.assertEqual(batch.formula_key(ode), batch.formula_key(other))
        other["ode_system"]["states"].append({"symbol": "a", "rhs": "-a"})
        self.assertNotEqual(batch.formula_key(ode), batch.formula_key(other))

    def test_collection_replaces_duplicates_and_rejections_and_resume_skips_completed_jobs(self):
        outcomes = iter(["a*x", "a*(x)", "reject", "a*x**2"])
        calls = []

        def fake_run(command, log, **kwargs):
            calls.append(command)
            output = Path(command[command.index("--output-dir") + 1])
            if command[2] == "srbench.generation.scenarios":
                count = int(command[command.index("--scenarios") + 1])
                path = output / "Equations" / "biology" / "equations.jsonl"
                path.parent.mkdir(parents=True)
                path.write_text("".join(json.dumps({"scenario_id": f"item_{i}"}) + "\n" for i in range(count)))
                return 0
            outcome = next(outcomes)
            if outcome == "reject":
                run = output / "candidate_test"
                run.mkdir(parents=True)
                batch._append_jsonl(run / "lineage_attempts.jsonl", {"status": "reject_not_novel"})
                return 1
            write_candidate(output, outcome)
            return 0

        with tempfile.TemporaryDirectory() as tmp, patch.object(batch, "_run", side_effect=fake_run), contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            batch.collect_subject(options(), "biology", root)
            records = batch._read_jsonl(root / "_checkpoints" / "biology" / "formulas.jsonl")
            self.assertEqual(len(records), 2)
            self.assertEqual(len({record["formula_key"] for record in records}), 2)
            ledger = batch._read_jsonl(root / "_checkpoints" / "biology" / "attempts.jsonl")
            self.assertEqual([item["status"] for item in ledger], ["accepted", "duplicate", "rejected", "accepted"])
            initial_call_count = len(calls)
            batch.collect_subject(options(), "biology", root)
            self.assertEqual(len(calls), initial_call_count)

    def test_completed_candidate_is_recovered_without_another_model_call(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp)
            round_dir = root / "_checkpoints" / "biology" / "round_001"
            batch._write_json(round_dir / "round.json", {"n_scenarios": 1})
            batch._write_json(round_dir / "generation_complete.json", {"n_equations": 1})
            equations = round_dir / "gen0" / "Equations" / "biology" / "equations.jsonl"
            equations.parent.mkdir(parents=True)
            equations.write_text(json.dumps({"scenario_id": "item_0"}) + "\n")
            write_candidate(round_dir / "evolved" / "job_001", "a*x")
            with patch.object(batch, "_run", side_effect=AssertionError("must reuse the completed candidate")):
                batch.collect_subject(options(target_per_subject=1), "biology", root)
            self.assertEqual(len(batch._read_jsonl(root / "_checkpoints" / "biology" / "formulas.jsonl")), 1)

    def test_pipeline_error_is_not_treated_as_scientific_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            audit = output / "candidate_test" / "lineage_attempts.jsonl"
            audit.parent.mkdir()
            batch._append_jsonl(audit, {"status": "reject_not_novel"})
            self.assertTrue(batch.expected_rejection(output))
            batch._append_jsonl(audit, {"status": "pipeline_error", "error": "provider outage"})
            self.assertFalse(batch.expected_rejection(output))

    def test_dry_run_creates_no_output_and_calls_no_model(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as output:
            args = ["run_candidate_batch.py", "--run-name", "preview", "--output-dir", tmp, "--dry-run"]
            with patch.object(sys, "argv", args), patch.object(batch, "_run", side_effect=AssertionError("dry run")):
                batch.main()
            plan = json.loads(output.getvalue())
            self.assertEqual(plan["config"]["target_per_subject"], 30)
            self.assertEqual(len(plan["first_round_commands"]), 2)
            self.assertFalse((Path(tmp) / "preview").exists())

    def test_only_subjects_is_execution_scope_and_preserves_full_scientific_config(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as output:
            batch.main(["--run-name", "physics-only", "--output-dir", tmp,
                        "--subjects", "biology", "physics", "--only-subjects", "physics", "--dry-run"])
            plan = json.loads(output.getvalue())
        self.assertEqual(plan["config"]["subjects"], ["biology", "physics"])
        self.assertNotIn("only_subjects", plan["config"])
        self.assertEqual(plan["execution"]["only_subjects"], ["physics"])
        self.assertEqual(len(plan["first_round_commands"]), 1)
        self.assertIn("physics", plan["first_round_commands"][0])

    def test_only_subjects_does_not_mark_the_full_run_complete(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            seen = []

            def collect(args, subject, root):
                seen.append(subject)
                path = root / "_checkpoints" / subject / "formulas.jsonl"
                path.parent.mkdir(parents=True, exist_ok=True)
                for index in range(args.target_per_subject):
                    batch._append_jsonl(path, {"formula_key": f"{subject}-{index}"})

            with patch.object(batch, "collect_subject", side_effect=collect):
                batch.main(["--run-name", "physics-only", "--output-dir", tmp,
                            "--subjects", "biology", "physics", "--only-subjects", "physics",
                            "--target-per-subject", "1"])
            status = json.loads((Path(tmp) / "physics-only/run.json").read_text())
        self.assertEqual(seen, ["physics"])
        self.assertEqual(status["status"], "incomplete")
        self.assertEqual(status["counts"], {"biology": 0, "physics": 1})

    def test_exhausted_budget_cannot_report_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            round_dir = root / "_checkpoints" / "biology" / "round_001"
            batch._write_json(round_dir / "round.json", {"n_scenarios": 1})
            batch._write_json(round_dir / "generation_complete.json", {"n_equations": 1})
            equations = round_dir / "gen0" / "Equations" / "biology" / "equations.jsonl"
            equations.parent.mkdir(parents=True)
            equations.write_text(json.dumps({"scenario_id": "item_0"}) + "\n")
            batch._append_jsonl(root / "_checkpoints" / "biology" / "attempts.jsonl", {
                "job_id": "offline/biology/001/item_0", "status": "rejected",
            })
            with self.assertRaisesRegex(RuntimeError, "requested count was NOT reached"):
                batch.collect_subject(options(max_rounds=1), "biology", root)


if __name__ == "__main__":
    unittest.main()
