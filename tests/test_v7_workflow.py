import contextlib
import copy
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
from srbench.common.contracts import contract_from_spec
from srbench.common.io import read_json, write_json, relative_artifact
from srbench.common.prediction import isolated_predictions
from srbench.common.metrics import regression_metrics
from srbench.generation import scenarios, evolution
from srbench.packaging.pipeline import build_package, main as package_main
from srbench.packaging.split import build_split
from srbench.packaging.reference import truth_values, reference_source, check_reference_source
from srbench.plotting.compare import compare

ROOT = Path(__file__).resolve().parents[1]


def fixture(name="static_1d"):
    return read_json(ROOT / "examples" / name / "spec.json")


class NaturalGenerationTests(unittest.TestCase):
    def test_scenario_generation_accepts_omitted_behavior_metadata_without_retry(self):
        static_spec = dict(
            model_family="static",
            target_symbol="F",
            target_description="restoring force",
            input_symbols=[dict(symbol="x", description="displacement", range=[-1.0, 1.0])],
        )
        ode_spec = dict(
            model_family="ode",
            target_symbol="dv_dt",
            target_description="acceleration",
            time_symbol="t",
            time_range=[0.0, 10.0],
            target_state="v",
            required_dynamic_states=[
                dict(symbol="x", description="displacement", initial_range=[-1.0, 1.0]),
                dict(symbol="v", description="velocity", initial_range=[-1.0, 1.0]),
            ],
        )
        caller = Mock()
        caller.complete.return_value = json.dumps({"scenarios": [
            dict(scenario_text="A spring", mechanism_tag="elastic",
                 functional_family="polynomial", spec=static_spec),
            dict(scenario_text="A mass on a spring", mechanism_tag="oscillator",
                 functional_family="oscillatory", spec=ode_spec),
        ]})
        generated = scenarios.generate_m2_for_subfield(
            caller, "physics", {"name": "classical_mechanics"}, 2, "offline", seed=7,
        )
        caller.complete.assert_called_once()
        self.assertEqual(len(generated), 2)
        for scene in generated:
            self.assertEqual(scene["spec"]["expected_behaviors"], [])
            self.assertEqual(scene["spec"]["forbidden_behaviors"], [])
        self.assertEqual(generated[0]["spec"]["input_symbols"], static_spec["input_symbols"])
        self.assertEqual(generated[1]["spec"]["required_dynamic_states"], ode_spec["required_dynamic_states"])

    def test_new_gen0_does_not_inherit_an_implicit_fixed_dimension(self):
        spec = dict(model_family="static", target_symbol="F", target_description="restoring force",
                    input_symbols=[dict(symbol="x", description="displacement", range=[0.0, 2.0])],
                    expected_behaviors=[], forbidden_behaviors=[])
        scene = scenarios.Scenario(scenario_text="A spring", mechanism_tag="elastic",
                                   functional_family="polynomial", spec=spec)
        self.assertNotIn("dimension_track", scene.model_dump())
        result = dict(equation_type="static_explicit", target_symbol="F", expression="-k*x",
                      symbols=["F", "x", "k"], symbol_descriptions=["force", "displacement", "stiffness"],
                      symbol_properties=["O", "V", "P"], derivation_notes="linear baseline",
                      dimension_class="fixed_univariate")
        caller = Mock()
        caller.complete.return_value = json.dumps(result)
        derived = scenarios.derive_equation(caller, "A spring", spec, "physics", "classical_mechanics", "offline")
        self.assertIsNone(derived["dimension_class"])
        derived["model_family"] = "static"
        changes = evolution._allowed_freedom_changes(derived, "extended", 4, 4)
        self.assertIn("add_input", changes)
        self.assertIn("parameter_to_input", changes)

    def test_packaged_taxonomy_resources_load(self):
        from srbench.generation.ontology import load_ontology
        content = load_ontology()
        encoded = json.dumps(content)
        self.assertIn("auxiliary_state_feedback", encoded)
        # This additionally checks the resources are available from the package.
        self.assertTrue((ROOT / "src/srbench/resources/taxonomy/subfield_taxonomy_v1.json").is_file())


class PackagingTests(unittest.TestCase):
    def test_one_dimensional_5000_points_and_disjoint_right_interval(self):
        spec = fixture()
        contract = contract_from_spec(spec)
        train, test, manifest = build_split(spec, contract, seed=11)
        self.assertEqual((len(train), len(test)), (4500, 500))
        self.assertAlmostEqual(train.x.max(), 4.5)
        self.assertGreater(test.x.min(), 4.5)
        self.assertEqual(test.x.max(), 5.0)
        self.assertEqual(list(train.columns), ["x", "F"])
        self.assertEqual(manifest["test_space_fraction"], 0.1)
        np.testing.assert_allclose(train.F, -2 * train.x / (1 + .08 * train.x**2))

    def test_log_axis_uses_log_coordinate_boundary(self):
        spec = fixture()
        spec["independent_variables"][0].update(range=[1.0, 100.0], scale="log")
        train, test, _ = build_split(spec, contract_from_spec(spec), n_total=100, test_points=10)
        self.assertAlmostEqual(train.x.max(), 10**1.8)
        self.assertGreater(test.x.min(), 10**1.8)

    def test_eight_dimensional_sobol_corner_volume_and_reproducibility(self):
        spec = fixture()
        names = [f"x{i}" for i in range(8)]
        spec["independent_variables"] = [{"symbol": n, "range": [0, 1]} for n in names]
        spec["parameters"] = []
        spec["rhs_for_integrator"] = "+".join(names)
        contract = contract_from_spec(spec)
        train, test, split = build_split(spec, contract, seed=17)
        boundary = split["normalized_boundary"]
        self.assertAlmostEqual((1 - boundary)**8, .1)
        self.assertTrue((test[names].to_numpy() > boundary).all())
        self.assertTrue((train[names].to_numpy() <= boundary).any(axis=1).all())
        self.assertEqual((len(train), len(test)), (4500, 500))
        again = build_split(spec, contract, seed=17)
        pd.testing.assert_frame_equal(test, again[1])
        different = build_split(spec, contract, seed=18)
        self.assertFalse(test.equals(different[1]))

    def test_ode_5000_points_keep_original_initial_conditions_and_derivative_target(self):
        spec = fixture("ode_system")
        contract = contract_from_spec(spec)
        train, test, split = build_split(spec, contract, seed=4)
        self.assertEqual(contract.features, ["t", "N", "R"])
        self.assertEqual(contract.target, "dN_dt")
        self.assertEqual((len(train), len(test)), (4500, 500))
        self.assertAlmostEqual(train.iloc[0].N, 1)
        self.assertGreater(test.t.min(), 7.2)
        self.assertGreater(test.iloc[0].N, 5)
        np.testing.assert_allclose(test.dN_dt, .8*test.N*test.R/(1+test.R)-.2*test.N)
        self.assertFalse(np.allclose(test.N, test.dN_dt))
        self.assertLess(abs(test.iloc[0].N-train.iloc[-1].N), .05)
        self.assertEqual(split["protocol"], "time_right_extrapolation")

    def test_reserved_symbol_names_are_preserved_in_standalone_reference(self):
        spec = fixture()
        spec["independent_variables"] = [{"symbol": "I", "range": [1, 2]}, {"symbol": "S", "range": [1, 3]}]
        spec["parameters"] = [{"symbol": "gamma", "value": 2}, {"symbol": "E", "value": 3}]
        spec["rhs_for_integrator"] = "gamma*I+E*S"
        contract = contract_from_spec(spec)
        train, test, _ = build_split(spec, contract, n_total=50, test_points=10)
        actual = check_reference_source(reference_source(contract), test, contract)
        np.testing.assert_allclose(actual, 2*test.I+3*test.S)

    def test_package_is_portable_and_oracle_has_no_agent_visible_truth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / "input.json"
            write_json(original, fixture())
            package = build_package(original, root / "02_packaged/spring", n_total=50, test_points=10)
            manifest = read_json(package / "manifest.json")
            self.assertEqual(manifest["oracle_self_test"]["test"]["versus_clean_truth"]["raw_r2"], 1.0)
            self.assertEqual(manifest["difficulty"], "unmeasured")
            self.assertEqual(set(p.name for p in (package / "task/environment").iterdir()), {"Dockerfile", "train_data.csv"})
            self.assertNotIn("-k*x", (package / "task/instruction.md").read_text())
            self.assertEqual((package / "task/tests/prediction.py").read_bytes(),
                             (ROOT / "src/srbench/common/prediction.py").read_bytes())
            for path in manifest["paths"].values():
                self.assertFalse(Path(path).is_absolute())
            original.unlink()
            moved = root / "moved"
            shutil.move(package, moved)
            output = compare(moved, moved / manifest["paths"]["reference"], root / "plots")
            metrics = read_json(output / "metrics.json")
            self.assertEqual(metrics["official_test_raw_r2"], 1.0)
            self.assertEqual(len(pd.read_csv(output / "predictions.csv")), 50)
            self.assertTrue((output / "comparison.pdf").is_file())

    def test_legacy_noise_setting_yields_clean_training_and_hidden_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            spec = fixture()
            spec["noise"] = .1
            source = Path(tmp) / "spec.json"
            write_json(source, spec)
            package = build_package(source, Path(tmp) / "noisy", n_total=100, test_points=20)
            manifest = read_json(package / "manifest.json")
            self.assertEqual(list(pd.read_csv(package / manifest["paths"]["train"]).columns), ["x", "F"])
            scores = manifest["oracle_self_test"]["test"]
            self.assertEqual(scores["versus_clean_truth"]["raw_r2"], 1)
            self.assertEqual(scores["versus_observed_label"]["raw_r2"], 1)
            self.assertEqual(manifest["oracle_self_test"]["train"]["versus_observed_label"]["raw_r2"], 1)
            self.assertEqual(read_json(package / "ground_truth.json")["spec"]["noise"], 0)
            self.assertEqual(read_json(package / "split_manifest.json")["label"], "clean_ground_truth")

    def test_identical_package_resume_and_modified_artifact_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "spec.json"
            write_json(source, fixture())
            destination = Path(tmp) / "package"
            build_package(source, destination, n_total=50, test_points=10)
            first = (destination / "manifest.json").read_bytes()
            build_package(source, destination, n_total=50, test_points=10, resume=True)
            self.assertEqual(first, (destination / "manifest.json").read_bytes())
            with self.assertRaisesRegex(ValueError, "differs"):
                build_package(source, destination, n_total=60, test_points=10, resume=True)
            (destination / "task/environment/train_data.csv").write_text("corrupted")
            with self.assertRaisesRegex(ValueError, "changed"):
                build_package(source, destination, n_total=50, test_points=10, resume=True)

    def test_packaging_batch_reads_canonical_index_without_checkpoints(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()):
            root = Path(tmp) / "run"
            write_json(root / "01_generated/biology_001/spec.json", fixture())
            (root / "01_generated/index.jsonl").write_text(json.dumps({
                "candidate_id": "biology_001", "spec": "01_generated/biology_001/spec.json"})+"\n")
            args = ["--run", str(root), "--n-total", "50", "--test-points", "10"]
            package_main(args)
            package_main(args+["--resume"])
            from datetime import date
            package_root = root / "02_packaged" / date.today().strftime("%Y%m%d")
            self.assertTrue((package_root / "biology_001/task/task.toml").exists())
            link = package_root / "harbor_dataset/biology_001"
            self.assertTrue(link.is_symlink())
            self.assertFalse(Path(os.readlink(link)).is_absolute())
            manifest = read_json(package_root / "biology_001/manifest.json")
            self.assertEqual(manifest["harbor_name"], "srbench-v7/biology_001")

    def test_provided_splits_are_reused_with_explicit_roles(self):
        spec = fixture()
        train, test, _ = build_split(spec, contract_from_spec(spec), n_total=50, test_points=10)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            train["irrelevant"] = 123
            train.to_csv(root / "train.csv", index=False)
            test.to_csv(root / "test.csv", index=False)
            actual, _, meta = build_split(spec, contract_from_spec(spec),
                train_csv=root / "train.csv", test_csv=root / "test.csv")
            self.assertEqual(list(actual.columns), ["x", "F"])
            self.assertEqual(len(actual), 40)
            self.assertEqual(meta["protocol"], "provided")

    def test_provided_noisy_targets_cannot_enter_clean_benchmark(self):
        spec = fixture()
        spec["noise"] = .5
        contract = contract_from_spec(spec)
        train, test, _ = build_split(spec, contract, n_total=50, test_points=10)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            train[contract.target + "_noisy"] = train[contract.target] + 100
            train.to_csv(root / "train.csv", index=False)
            test.to_csv(root / "test.csv", index=False)
            clean, _, _ = build_split(spec, contract, train_csv=root / "train.csv", test_csv=root / "test.csv")
            np.testing.assert_allclose(clean[contract.target], truth_values(contract, clean))
            test[contract.target] += 1
            test.to_csv(root / "test.csv", index=False)
            with self.assertRaisesRegex(ValueError, "does not match"):
                build_split(spec, contract, train_csv=root / "train.csv", test_csv=root / "test.csv")

    def test_unsupported_implicit_model_is_not_silently_packaged(self):
        spec = fixture()
        spec["integrator"] = "root_solve_implicit"
        with self.assertRaisesRegex(ValueError, "explicit branch"):
            contract_from_spec(spec)

    def test_hidden_constant_target_cannot_claim_valid_r2(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "spec.json"
            spec = fixture()
            spec["rhs_for_integrator"] = "2"
            write_json(source, spec)
            with self.assertRaisesRegex(ValueError, "near-zero variance"):
                build_package(source, Path(tmp) / "bad", n_total=50, test_points=10)
            self.assertFalse((Path(tmp) / "bad").exists())

    def test_standalone_verifier_runs_without_original_source_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "spec.json"
            write_json(source, fixture())
            package = build_package(source, root / "pack", n_total=50, test_points=10)
            tests = package / "task/tests"
            code = "import sys,test_outputs; sys.exit(test_outputs.evaluate(*sys.argv[1:],drop_privileges=False))"
            args = [sys.executable, "-c", code, str(package / "task/solution/reference_law.py"),
                    str(tests / "test_data.csv"), str(tests / "contract.json"), str(root / "logs")]
            completed = subprocess.run(args, cwd=tests, text=True, capture_output=True)
            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertEqual(read_json(root / "logs/metrics.json")["raw_r2"], 1)
            self.assertTrue((tests / "test_data.csv").exists())


class ProviderConfigurationTests(unittest.TestCase):
    def test_http_requests_send_only_the_selected_nonempty_auth_header(self):
        import anthropic
        import httpx
        from srbench.common.model_provider import _anthropic_kwargs

        environment = {"ANTHROPIC_API_KEY": "inherited-key",
                       "ANTHROPIC_AUTH_TOKEN": "inherited-token"}
        for source, key, token, expected in (
            ("api_key", "explicit-key", "explicit-token", "api_key"),
            ("auth_token", "explicit-key", "explicit-token", "auth_token"),
            ("auto", "explicit-key", "explicit-token", "api_key"),
            ("auto", None, "explicit-token", "auth_token"),
        ):
            with self.subTest(source=source, expected=expected):
                requests = []

                def respond(request):
                    requests.append(request)
                    return httpx.Response(200, json={
                        "id": "msg_test", "type": "message", "role": "assistant",
                        "model": "test-model", "content": [{"type": "text", "text": "OK"}],
                        "stop_reason": "end_turn", "stop_sequence": None,
                        "usage": {"input_tokens": 1, "output_tokens": 1},
                    })

                with patch.dict(os.environ, environment, clear=True):
                    kwargs = _anthropic_kwargs(key, token, "https://provider.invalid", source)
                    with anthropic.Anthropic(**kwargs, max_retries=0,
                            http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
                        response = client.messages.create(model="test-model", max_tokens=8,
                            messages=[{"role": "user", "content": "Reply OK"}])
                self.assertEqual(response.content[0].text, "OK")
                self.assertEqual(len(requests), 1)
                headers = requests[0].headers
                if expected == "api_key":
                    self.assertEqual(headers["x-api-key"], "explicit-key")
                    self.assertNotIn("authorization", headers)
                else:
                    self.assertEqual(headers["authorization"], "Bearer explicit-token")
                    self.assertNotIn("x-api-key", headers)

    def test_sdk_and_text_stages_use_the_same_endpoint_and_selected_credential(self):
        from srbench.common.model_provider import anthropic_runtime_env, _anthropic_kwargs
        environment = {"ANTHROPIC_API_KEY": "fake-key", "ANTHROPIC_AUTH_TOKEN": "fake-token",
                       "ANTHROPIC_BASE_URL": "https://environment.invalid"}
        with patch.dict(os.environ, environment, clear=True):
            env = anthropic_runtime_env("https://argument.invalid", "auth_token")
            self.assertEqual(env["ANTHROPIC_BASE_URL"], "https://argument.invalid")
            self.assertEqual(env["ANTHROPIC_AUTH_TOKEN"], "fake-token")
            self.assertEqual(env["ANTHROPIC_API_KEY"], "")
            self.assertEqual(anthropic_runtime_env()["ANTHROPIC_API_KEY"], "fake-key")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "fake-key"}, clear=True):
            self.assertEqual(anthropic_runtime_env()["ANTHROPIC_BASE_URL"], "https://api.anthropic.com")
        sdk = _anthropic_kwargs("fake-key", "fake-token", "https://argument.invalid", "auth_token")
        scene, selected = scenarios._build_client_kwargs("fake-key", "fake-token", "https://argument.invalid", "auth_token")
        self.assertEqual(sdk, scene)
        self.assertEqual(selected, "auth_token")

    def test_dataspec_entry_forwards_endpoint_and_auth_selection(self):
        from srbench.generation import data_spec
        with patch.object(data_spec, "plan_data_generation_async", new_callable=AsyncMock, return_value={}) as plan:
            data_spec.plan_data_generation({}, "physics", base_url="https://argument.invalid", auth_source="auth_token")
            plan.assert_awaited_once_with({}, "physics", base_url="https://argument.invalid", auth_source="auth_token")


class PredictionAndPlotTests(unittest.TestCase):
    def test_single_row_calls_do_not_share_mutable_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "law.py"
            path.write_text("count=0\ndef law(rows):\n global count\n assert len(rows)==1\n count+=1\n return [count]\n")
            result = isolated_predictions(path, [{"x": i} for i in range(5)], "F")
            self.assertTrue(result.ok, result.errors)
            self.assertEqual(result.values, [1.] * 5)

    def test_import_failures_and_nonfinite_outputs_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "law.py"
            for source in ("raise RuntimeError('broken import')", "def law(rows): return [float('nan')]"):
                with self.subTest(source=source):
                    path.write_text(source)
                    result = isolated_predictions(path, [{"x": 1}], "F")
                    self.assertFalse(result.ok)
                    self.assertEqual(len(result.errors), 1)

    def test_wrong_law_has_raw_negative_r2_and_separate_train_test_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "spec.json"
            write_json(source, fixture())
            package = build_package(source, root / "02_packaged/spring", n_total=50, test_points=10)
            output = compare(package, ROOT / "examples/static_1d/law.py")
            report = read_json(output / "metrics.json")
            self.assertLess(report["official_test_raw_r2"], -1)
            self.assertEqual(set(report["partitions"]), {"train", "test"})
            from datetime import datetime
            self.assertEqual(output, (root / "03_plots" / f"LLM_vs_truth_{datetime.now():%Y%m%d}" / "spring").resolve())
            self.assertEqual(regression_metrics([100, 100], [1, 2])["raw_r2"], -38809)

    def test_failed_law_writes_full_prediction_table_without_partial_score(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "spec.json"
            write_json(source, fixture())
            package = build_package(source, root / "pack", n_total=50, test_points=10)
            law = root / "bad.py"
            law.write_text("def law(rows): return [float('inf')]")
            with self.assertRaisesRegex(RuntimeError, "submitted law failed"):
                compare(package, law, root / "plots")
            report = read_json(root / "plots/metrics.json")
            self.assertEqual(report["status"], "prediction_failed")
            self.assertIsNone(report["scores"])
            self.assertEqual(len(pd.read_csv(root / "plots/predictions.csv")), 50)
            self.assertFalse((root / "plots/comparison.png").exists())


if __name__ == "__main__":
    unittest.main()
