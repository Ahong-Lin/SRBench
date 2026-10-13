import copy
import json
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import numpy as np

from srbench.common.io import read_json, read_jsonl
from srbench.common.contracts import contract_from_spec
from srbench.common.model_provider import ModelRequestError
from srbench.generation import evolution, pipeline, data_spec, scenarios
from srbench.generation.data_generator import gen_evaluate_explicit, _lambdify
from srbench.packaging.reference import reference_source, check_reference_source
from test_freedom_evolution import static_parent, child_with_freedom, plan_for


class EvolutionDiagnosticsTests(unittest.TestCase):
    def test_malformed_expression_without_predicates_retries_the_current_step(self):
        parent = static_parent()
        child = child_with_freedom(parent, "add_input")
        child["expression"] = "a*x + x*z*Heaviside(x, 1)"
        child["evolution_contract"]["after_fragment"] = child["expression"]
        bad = copy.deepcopy(child)
        bad["expression"] += ")"
        bad["evolution_contract"]["after_fragment"] = bad["expression"]
        caller = Mock()
        caller.complete.side_effect = [json.dumps(bad), json.dumps(child)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "calls.jsonl"
            result = evolution.evolve_once(
                caller, parent, "change_assumption", "science", "scenario", "offline",
                str.strip, "extended", 4, 4, max_retries=1, trace_path=path,
            )
            calls = read_jsonl(path)
        self.assertEqual(result["expression"], child["expression"])
        self.assertEqual([row["status"] for row in calls], ["error", "accepted"])
        self.assertIn("invalid expression syntax", calls[0]["error"])
        self.assertIn("invalid expression syntax", calls[1]["prompt"])
        self.assertEqual(caller.complete.call_count, 2)

    def test_piecewise_eq_condition_survives_validation_tools_data_and_reference(self):
        parent = static_parent()
        child = child_with_freedom(parent, "add_input")
        child["expression"] = "Piecewise((a*x, Eq(z, 0)), (a*x + x*z, True))"
        child["evolution_contract"]["after_fragment"] = child["expression"]
        validated, _ = evolution._normalize_and_validate_evolved(parent, child, "change_assumption", "extended", 4, 4)
        _, unknown = scenarios._expression_names(child["expression"], set(child["symbols"]))
        self.assertFalse(unknown)
        parsed = data_spec._sympify(validated["expression"])
        self.assertEqual({str(s) for s in parsed.free_symbols}, {"a", "x", "z"})
        spec = dict(equation_type="explicit", integrator="evaluate_explicit", dependent_variable="y",
                    rhs_for_integrator=validated["expression"],
                    independent_variables=[{"symbol": "x", "range": [0, 2], "n_points": 5000},
                                           {"symbol": "z", "range": [0, 1], "n_points": 5000}],
                    parameters=[{"symbol": "a", "value": 2}], noise=0, _n_total=5000)
        import pandas as pd
        columns, values = gen_evaluate_explicit(spec, seed=1)
        frame = pd.DataFrame(values, columns=columns)
        self.assertEqual(len(frame), 5000)
        np.testing.assert_allclose(frame.y, 2*frame.x + frame.x*frame.z)
        # Explicitly exercise both the zero-parameter and positive branches.
        points = pd.DataFrame({"x": [1., 1.], "z": [0., 1.]})
        contract = contract_from_spec(spec)
        np.testing.assert_allclose(check_reference_source(reference_source(contract), points, contract), [2., 3.])

    def test_boolean_equations_cannot_masquerade_as_numeric_rhs(self):
        for expression in ("Eq(y, a*x)", "a*x + Eq(x, 0)", "Piecewise((Eq(y, a*x), x > 0), (0, True))"):
            with self.subTest(expression=expression):
                with self.assertRaisesRegex(evolution.EvolvedEquationValidationError, "only inside a Piecewise"):
                    evolution._extract_expression_names(expression, {"a", "x", "y"})
                with self.assertRaisesRegex(ValueError, "only inside a Piecewise"):
                    data_spec._sympify(expression)
                with self.assertRaisesRegex(ValueError, "only inside a Piecewise"):
                    _lambdify(expression, ["x", "a"])

    def test_combined_piecewise_conditions_and_unknown_functions_remain_distinct(self):
        expr = "Piecewise((x, And(Ge(x, 0), Ne(x, 1))), (-x, True))"
        used, unknown = evolution._extract_expression_names(expr, {"x"})
        self.assertEqual(used, {"x"})
        self.assertFalse(unknown)
        fn, _ = _lambdify(expr, ["x"])
        np.testing.assert_allclose(fn(np.array([-2., 0., 1., 2.])), [2., 0., -1., 2.])
        self.assertIn("unmodeled", evolution._extract_expression_names("unmodeled(x)", {"x"})[1])

    def test_failed_and_accepted_model_outputs_are_both_retained(self):
        parent = static_parent()
        child = child_with_freedom(parent, "add_input")
        bad = copy.deepcopy(child)
        bad["evolution_contract"]["after_fragment"] = "not_in_child"
        caller = Mock()
        caller.complete.side_effect = [json.dumps(bad), json.dumps(child)]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "calls.jsonl"
            result = evolution.evolve_once(caller, parent, "change_assumption", "science", "scenario", "offline",
                str.strip, "extended", 4, 4, max_retries=1, trace_path=path)
            calls = read_jsonl(path)
        self.assertEqual(result["expression"], child["expression"])
        self.assertEqual([row["status"] for row in calls], ["error", "accepted"])
        self.assertIn("after_fragment", calls[0]["error"])
        self.assertEqual(json.loads(calls[0]["raw_response"]), bad)
        self.assertEqual(json.loads(calls[1]["raw_response"]), child)
        self.assertIn("not_in_child", calls[1]["prompt"])
        self.assertTrue(all(row["elapsed_seconds"] >= 0 for row in calls))

    def test_completed_generation_is_saved_when_later_generation_fails(self):
        parent = static_parent()
        child = child_with_freedom(parent, "add_input")
        args = SimpleNamespace(max_steps=2, steps=2, operation_policy="guided", discipline="science",
                               model="offline", novelty_model=None, assumption_mode="extended",
                               max_static_input_dim=4, max_ode_state_dim=4)
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(evolution, "plan_evolution_step", return_value=plan_for(child)), \
                patch.object(evolution, "evolve_once", side_effect=[child, ModelRequestError("service unavailable")]):
            directory = Path(tmp)
            with self.assertRaisesRegex(ModelRequestError, "service unavailable"):
                pipeline._lineage(parent, "demo", Mock(), args, random.Random(0), None, checkpoint_dir=directory)
            lineage = read_jsonl(directory / "lineage.jsonl")
            progress = read_json(directory / "progress.json")
            selection = read_json(directory / "gen_002_selection.json")
        self.assertEqual([row["generation"] for row in lineage], [0, 1])
        self.assertEqual(lineage[-1]["expression"], child["expression"])
        self.assertEqual(progress["completed_generations"], 1)
        self.assertEqual((progress["generation"], progress["stage"]), (2, "evolving"))
        self.assertEqual(selection["operation"], "change_assumption")

    def test_plan_failure_saves_response_without_disguising_it_as_scientific_rejection(self):
        caller = Mock()
        caller.complete.return_value = "invalid JSON"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.jsonl"
            with self.assertRaises(json.JSONDecodeError):
                evolution.plan_evolution_step(caller, static_parent(), "science", "scenario", "offline", str.strip,
                                               max_retries=0, trace_path=path)
            calls = read_jsonl(path)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["raw_response"], "invalid JSON")
        self.assertEqual(calls[0]["status"], "error")


if __name__ == "__main__":
    unittest.main()
