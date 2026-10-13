"""A failed numeric probe must not prevent saving a later usable DataSpec."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from srbench.common.io import read_json, write_json
from srbench.generation import data_spec, pipeline


class DataSpecDiagnosticsTests(unittest.TestCase):
    def test_explicit_spec_rejects_undeclared_rhs_symbols(self):
        spec = data_spec.DataGenSpec.model_validate({
            "equation_type": "explicit", "integrator": "evaluate_explicit",
            "dependent_variable": "H_g",
            "independent_variables": [
                {"symbol": name, "range": [1, 2]}
                for name in ("H0", "Ne", "g", "mu")
            ],
            "parameters": [],
            "rhs_for_integrator": "H0*exp(-(4*m + 1/(2*N))*g)",
        })
        with self.assertRaisesRegex(ValueError, "undeclared symbols: N, m"):
            data_spec._validate_emitted_spec(spec)
        spec.rhs_for_integrator = "H0*exp(-(4*mu + 1/(2*Ne))*g)"
        data_spec._validate_emitted_spec(spec)

    def test_nonfinite_probe_results_are_strict_json_with_explicit_verdicts(self):
        for expression, x, expected in (
            ("1/x", 0, "nan"),
            ("exp(x)", 1000, "inf"),
            ("-exp(x)", 1000, "-inf"),
        ):
            with self.subTest(expression=expression):
                result = data_spec._check_substitution(expression, {"x": x}, "y")
                self.assertEqual(result["verdict"], "non_finite")
                self.assertFalse(result["is_finite"])
                encoded = json.dumps(result, allow_nan=False)
                self.assertEqual(json.loads(encoded)["value_real"], expected)

    def test_finite_and_complex_probe_values_remain_numeric(self):
        for expression, x, real, imaginary, verdict in (
            ("1/x", 2, 0.5, 0.0, "ok"),
            ("sqrt(x)", -1, 0.0, 1.0, "complex"),
        ):
            with self.subTest(expression=expression):
                result = data_spec._check_substitution(expression, {"x": x}, "y")
                self.assertEqual((result["value_real"], result["value_imag"]), (real, imaginary))
                self.assertEqual(result["verdict"], verdict)
                self.assertTrue(result["is_finite"])

    def test_substitution_timeout_returns_without_repeating_symbolic_work(self):
        with patch("sympy.N", side_effect=lambda value: time.sleep(2)):
            result = data_spec._check_substitution(
                "x + 1", {"x": 2}, "y", timeout_seconds=1,
            )
        self.assertFalse(result["ok"])
        self.assertEqual(result["error"], "evaluation timed out after 1s")
        self.assertEqual(result["residual_free_symbols"], [])

    def test_bad_probe_then_valid_spec_can_be_saved_and_generate_finite_data(self):
        record = {
            "model_family": "static", "equation_type": "static_explicit",
            "target_symbol": "y", "expression": "1/x",
            "symbols": ["y", "x"], "symbol_properties": ["O", "V"],
            "symbol_descriptions": ["response", "input"],
            "evolution_contract": {"freedom_change": "none"},
        }
        emitted = {
            "equation_type": "explicit", "integrator": "evaluate_explicit",
            "dependent_variable": "y", "rhs_for_integrator": "1/x",
            "independent_variables": [{"symbol": "x", "range": [1, 2], "n_points": 32, "scale": "linear"}],
            "parameters": [],
        }
        tool_calls = [
            ("analyze_expression", {"expression": "1/x", "target_symbol": "y"}),
            ("check_substitution", {"expression": "1/x", "assignments": {"x": 0}, "target_symbol": "y"}),
            ("check_substitution", {"expression": "1/x", "assignments": {"x": 1.5}, "target_symbol": "y"}),
            ("emit_data_gen_spec", emitted),
        ]
        for provider in ("openai", "openrouter"):
            with self.subTest(provider=provider), tempfile.TemporaryDirectory() as tmp:
                requests = []

                def respond(**kwargs):
                    requests.append(copy.deepcopy(kwargs))
                    name, args = tool_calls[len(requests) - 1]
                    return {"choices": [{"message": {"tool_calls": [{
                        "id": str(len(requests)), "type": "function",
                        "function": {"name": name, "arguments": json.dumps(args)},
                    }]}}]}

                caller = Mock()
                caller.chat.side_effect = respond
                with patch.object(data_spec, "build_model_caller", return_value=caller):
                    result = data_spec.plan_data_generation_chat(
                        record, "science", provider=provider, model="offline",
                        max_turns=4, verbose=False,
                    )
                path = Path(tmp) / "planned_spec.json"
                write_json(path, result)
                saved = read_json(path)
                probes = [item["result"] for item in saved["_trace"]
                          if item.get("tool") == "check_substitution"]
                self.assertEqual([item["verdict"] for item in probes], ["non_finite", "ok"])
                self.assertEqual(saved["rhs_for_integrator"], record["expression"])
                self.assertEqual(saved["independent_variables"], emitted["independent_variables"])
                feedback = json.loads(requests[2]["messages"][-1]["content"])
                self.assertEqual(feedback["value_real"], "nan")
                self.assertEqual(feedback["verdict"], "non_finite")
                self.assertEqual(caller.chat.call_count, 4)
                _, csv_path = pipeline._generate(saved, "offline", 5, Path(tmp) / "data", 7, 32)
                values = np.loadtxt(csv_path, delimiter=",", skiprows=1, ndmin=2)
                self.assertEqual(values.shape, (32, 2))
                self.assertTrue(np.isfinite(values).all())
                np.testing.assert_allclose(values[:, 1], 1 / values[:, 0])

    def test_strict_writer_still_rejects_nonfinite_computational_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            for value in (float("nan"), float("inf"), float("-inf")):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    write_json(Path(tmp) / "invalid_spec.json", {
                        "parameters": [{"symbol": "a", "value": value}],
                    })


if __name__ == "__main__":
    unittest.main()
