import copy
import asyncio
import json
import random
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from srbench.generation import evolution as evolve
from srbench.generation import data_spec as spec_agent
from srbench.generation import pipeline
import numpy as np
from srbench.generation.data_generator import gen_evaluate_explicit, gen_integrate_system
from srbench.generation.ontology import compatible_embedding_patterns


def static_parent():
    return {
        "model_family": "static", "equation_type": "static_explicit",
        "target_symbol": "y", "expression": "a*x", "symbols": ["y", "x", "a"],
        "symbol_properties": ["O", "V", "P"],
        "symbol_descriptions": ["response", "controlled input", "response coefficient"],
    }


def ode_parent():
    return {
        "model_family": "ode", "equation_type": "ode_system",
        "target_symbol": "dN", "expression": "r*N", "symbols": ["dN", "t", "N", "r"],
        "symbol_properties": ["O", "V", "S", "P"],
        "symbol_descriptions": ["population rate", "time", "population", "growth rate"],
        "ode_system": {"time_symbol": "t", "target_state": "N", "states": [
            {"symbol": "N", "rhs": "r*N", "initial_condition": 1.0, "description": "population"},
        ]},
    }


def child_with_freedom(parent, change, operation="change_assumption"):
    child = copy.deepcopy(parent)
    is_static = parent["model_family"] == "static"
    promotion = change.startswith("parameter_to_")
    quantity = ("a" if is_static else "r") if promotion else "z"
    new_role = "V" if is_static else "S"
    if promotion:
        child["symbol_properties"][child["symbols"].index(quantity)] = new_role
    else:
        child["symbols"].append(quantity)
        child["symbol_properties"].append(new_role)
        child["symbol_descriptions"].append("external condition" if is_static else "relaxing resource")
    child["new_symbol_range_suggestions"] = {quantity: "[0.1, 2]"}
    if is_static:
        child["expression"] = "a*x" if promotion else "a*x + x*z"
        if operation == "add_term" and promotion:
            child["expression"] += " + a*x**2"
    else:
        if not promotion:
            child["expression"] += " - N*z"
        elif operation == "add_term":
            child["expression"] += " - N**2"
        child["ode_system"]["states"][0]["rhs"] = child["expression"]
        child["symbols"].extend(["q", "tau"])
        child["symbol_properties"].extend(["P", "P"])
        child["symbol_descriptions"].extend(["equilibrium resource or rate", "relaxation time"])
        child["new_symbol_range_suggestions"].update({"q": "[0.1, 1]", "tau": "[1, 3]"})
        child["ode_system"]["states"].append({
            "symbol": quantity, "rhs": f"(q - {quantity})/tau",
            "initial_condition": 0.2, "description": "finite relaxation of resource or growth rate",
        })
    contract = {
        "operation": operation, "freedom_change": change,
        "promoted_symbol": quantity if promotion else None,
        "promotion_reason": "a fixed condition cannot describe the varying experimental conditions",
        "scope_kind": "pairwise", "scope_symbols": ["x" if is_static else "N", quantity],
        "structural_role": "modulation", "domain_mechanism": "finite environmental response",
        "scientific_mechanism": "finite environmental response", "embedding_pattern": "state_coupling",
        "difficulty_rationale": "response depends on the varying condition",
        "assumption_before": "fixed environment", "assumption_after": "variable environment",
        "before_fragment": parent["expression"], "after_fragment": child["expression"],
        "parent_reduction": "hold the released quantity at its reference and remove the added process",
        "observable_signature": "response changes with the condition",
        "shortcut_blocked": "one constant cannot represent several controlled conditions",
    }
    child.update({
        "evolution_contract": contract, "derivation_notes": "release the scientifically relevant condition",
        "change_summary": "resolve varying conditions explicitly", "assumption_audit": None,
        "add_term_audit": None,
    })
    if operation == "add_term":
        child["add_term_audit"] = {
            "mechanism_class": "environmental response", "mechanism_claim": "an omitted environmental process",
            "parent_reduction": contract["parent_reduction"], "observable_signature": contract["observable_signature"],
        }
    else:
        child["assumption_audit"] = {
            "released_assumption": "fixed condition",
            "outcome": "condition_promotion" if is_static else "state_augmentation",
            "quantity": quantity, "quantity_role": "controlled_input" if is_static else "internal_state",
            "mechanism": contract["scientific_mechanism"],
            "reference_condition": {quantity: 1.0 if promotion else 0.0} if is_static else {},
            "parent_reduction": contract["parent_reduction"],
        }
    return child


def plan_for(child):
    contract = child["evolution_contract"]
    return {
        **{key: contract[key] for key in ("operation", "freedom_change", "promoted_symbol", "promotion_reason", "scientific_mechanism")},
        "gap_statement": "fixed environment omits experimental variation",
        "baseline_assumption": "fixed environment",
        "affected_symbols": [contract["promoted_symbol"] or contract["scope_symbols"][0]],
        "rationale": "the next model resolves the variable environment",
    }


def validate(parent, child, **limits):
    return evolve._normalize_and_validate_evolved(
        parent, child, child["evolution_contract"]["operation"],
        limits.get("assumption_mode", "extended"), limits.get("max_static_inputs", 4),
        limits.get("max_ode_states", 4), dimension_track=limits.get("dimension_track"),
    )[0]


def data_spec(child):
    ode = child.get("ode_system")
    roles = dict(zip(child["symbols"], child["symbol_properties"]))
    values = {"a": 1.0, "r": 0.2, "q": 0.6, "tau": 1.0}
    spec = spec_agent.DataGenSpec(
        equation_type="ode_system" if ode else "explicit",
        integrator="integrate_system" if ode else "evaluate_explicit",
        dependent_variable=ode["target_state"] if ode else child["target_symbol"],
        rhs_for_integrator=child["expression"],
        independent_variables=[{"symbol": name, "range": [0.1, 2.0], "n_points": 64}
                               for name, role in roles.items() if role == "V"],
        parameters=[{"symbol": name, "value": values[name]} for name, role in roles.items() if role == "P"],
        state_variables=[state["symbol"] for state in ode["states"]] if ode else [],
        state_rhs=[state["rhs"] for state in ode["states"]] if ode else [],
        initial_conditions={state["symbol"]: state["initial_condition"] for state in ode["states"]} if ode else {},
    )
    return spec


class FreedomEvolutionTests(unittest.TestCase):
    def test_both_operations_support_new_quantities_and_literal_parameter_promotions(self):
        for operation in ("add_term", "change_assumption"):
            for change, parent in (("add_input", static_parent()), ("parameter_to_input", static_parent()),
                                   ("add_state", ode_parent()), ("parameter_to_state", ode_parent())):
                with self.subTest(operation=operation, change=change):
                    child = child_with_freedom(parent, change, operation)
                    result = validate(parent, evolve.EvolvedEquation.model_validate(child).model_dump())
                    roles = evolve._split_roles(result)
                    self.assertEqual(len(roles["independent_variables"] if parent["model_family"] == "static"
                                         else roles["state_variables"]), 2)
                    self.assertEqual(result["evolution_contract"]["freedom_change"], change)

    def test_roles_and_metadata_must_agree(self):
        for change, promoted in (("none", None), ("parameter_to_input", "a")):
            with self.subTest(change=change):
                child = child_with_freedom(static_parent(), "add_input")
                child["evolution_contract"].update(freedom_change=change, promoted_symbol=promoted)
                with self.assertRaisesRegex(ValueError, "freedom_change must match symbol roles"):
                    validate(static_parent(), child)

    def test_promotion_requires_the_actual_parent_parameter_and_range(self):
        child = child_with_freedom(static_parent(), "parameter_to_input")
        child["evolution_contract"]["promoted_symbol"] = "x"
        with self.assertRaisesRegex(ValueError, "existing P"):
            validate(static_parent(), child)
        child["evolution_contract"]["promoted_symbol"] = "a"
        child["new_symbol_range_suggestions"] = {}
        with self.assertRaisesRegex(ValueError, "suggested range"):
            validate(static_parent(), child)

    def test_one_freedom_per_step_and_existing_dimension_limits(self):
        child = child_with_freedom(static_parent(), "add_input")
        for limits in ({"max_static_inputs": 1}, {"assumption_mode": "core"}, {"dimension_track": "fixed_univariate"}):
            with self.subTest(limits=limits), self.assertRaises(ValueError):
                validate(static_parent(), child, **limits)
        child["symbol_properties"][child["symbols"].index("a")] = "V"
        with self.assertRaisesRegex(ValueError, "at most one"):
            validate(static_parent(), child)
        with self.assertRaisesRegex(ValueError, "1-1 states"):
            validate(ode_parent(), child_with_freedom(ode_parent(), "add_state"), max_ode_states=1)

    def test_new_state_requires_closure_and_old_initial_conditions_are_preserved(self):
        child = child_with_freedom(ode_parent(), "add_state", "add_term")
        incomplete = copy.deepcopy(child)
        incomplete["ode_system"]["states"].pop()
        with self.assertRaisesRegex(ValueError, "S symbols"):
            validate(ode_parent(), incomplete)
        child["ode_system"]["states"][0]["initial_condition"] = 2.0
        with self.assertRaisesRegex(ValueError, "initial conditions"):
            validate(ode_parent(), child)

    def test_isolated_added_state_is_rejected_but_one_way_influence_is_allowed(self):
        parent = ode_parent()
        child = child_with_freedom(parent, "add_state")
        validate(parent, child)  # new RHS does not reference the old state
        child["expression"] = parent["expression"]
        child["ode_system"]["states"][0]["rhs"] = child["expression"]
        with self.assertRaisesRegex(ValueError, "influence an existing"):
            validate(parent, child)

    def test_planning_can_name_a_parameter_and_respects_family_and_budget(self):
        parent = static_parent()
        plan = plan_for(child_with_freedom(parent, "parameter_to_input"))
        caller = Mock()
        caller.complete.return_value = json.dumps(plan)
        kwargs = dict(caller=caller, current=parent, discipline="science", scenario_text="varying environment",
                      model="offline", strip_fence=evolve._strip_code_fence, max_retries=0)
        self.assertEqual(evolve.plan_evolution_step(**kwargs), plan)
        with self.assertRaisesRegex(ValueError, "incompatible"):
            evolve.plan_evolution_step(**kwargs, max_static_inputs=1)
        self.assertIn("ALLOWED freedom_change VALUES FOR THIS PARENT: none", caller.complete.call_args.args[0])
        caller.complete.return_value = json.dumps(plan | {"affected_symbols": ["r"], "promoted_symbol": "r"})
        with self.assertRaisesRegex(ValueError, "incompatible"):
            evolve.plan_evolution_step(**(kwargs | {"current": ode_parent()}))

    def test_embedding_uses_planned_quantity_with_original_weights(self):
        plan = plan_for(child_with_freedom(static_parent(), "add_input", "add_term"))
        rng = Mock()
        rng.choices.side_effect = lambda choices, **kwargs: [next(c for c in choices if c["id"] == "state_coupling")]
        chosen = evolve.sample_embedding_pattern(rng, static_parent(), "add_term", evolution_plan=plan)
        expected = compatible_embedding_patterns("add_term", "static", 2)
        self.assertEqual(chosen["id"], "state_coupling")
        self.assertEqual(rng.choices.call_args.args[0], expected)
        self.assertEqual(rng.choices.call_args.kwargs["weights"], [c["weight"] for c in expected])
        choices = [evolve.sample_embedding_pattern(random.Random(i), ode_parent(), "change_assumption",
                   evolution_plan={"freedom_change": "none"})["id"] for i in range(20)]
        self.assertNotIn("auxiliary_state_feedback", choices)

    def test_mocked_evolution_and_lineage_keep_freedom_metadata(self):
        parent = static_parent()
        child = child_with_freedom(parent, "parameter_to_input")
        plan = plan_for(child)
        caller = Mock()
        caller.complete.side_effect = [json.dumps(plan), json.dumps(child)]
        planned = evolve.plan_evolution_step(caller, parent, "science", "controlled response", "offline", str.strip)
        result = evolve.evolve_once(caller, parent, plan["operation"], "science", "controlled response", "offline",
                                    str.strip, "extended", 4, 4, evolution_plan=planned,
                                    embedding_pattern={"id": "state_coupling"}, max_retries=0)
        prompt = caller.complete.call_args.args[0]
        self.assertNotIn('"evolution_contract": {{', prompt)
        record = evolve._record(result, "demo", 1, plan["operation"], "controlled response")
        self.assertEqual(record["promoted_symbol"], "a")
        self.assertEqual(record["evolution_plan"], plan)
        self.assertEqual(record["parameters"], [])
        self.assertIsNone(record["dimension_track"])
        self.assertEqual(json.loads(json.dumps(record))["freedom_change"], "parameter_to_input")

    def test_child_cannot_silently_change_planned_freedom(self):
        parent = static_parent()
        child = child_with_freedom(parent, "add_input")
        plan = plan_for(child) | {"freedom_change": "none", "promotion_reason": ""}
        caller = Mock()
        caller.complete.return_value = json.dumps(child)
        with self.assertRaisesRegex(ValueError, "must match the first-layer plan"):
            evolve.evolve_once(caller, parent, plan["operation"], "science", "scenario", "offline", str.strip,
                               "extended", 4, 4, evolution_plan=plan, max_retries=0)

    def test_pipeline_passes_freedom_plan_into_embedding_and_lineage(self):
        parent = static_parent()
        child = child_with_freedom(parent, "parameter_to_input")
        plan = plan_for(child)
        embedding = evolve.sample_embedding_pattern(random.Random(3), parent, plan["operation"], evolution_plan=plan)
        child["evolution_contract"]["embedding_pattern"] = embedding["id"]
        caller = Mock()
        caller.complete.side_effect = [json.dumps(plan), json.dumps(child)]
        args = SimpleNamespace(max_steps=1, steps=1, operation_policy="guided", discipline="science",
                               model="offline", novelty_model=None, assumption_mode="extended",
                               max_static_input_dim=2, max_ode_state_dim=4)
        with patch("srbench.generation.novelty.check_novelty", side_effect=AssertionError("novelty disabled")):
            lineage, novelty = pipeline._lineage(parent, "demo", caller, args, random.Random(3), None)
        self.assertEqual(novelty["answer"], "NOT_EVALUATED")
        self.assertEqual(lineage[-1]["freedom_change"], "parameter_to_input")
        self.assertEqual(lineage[-1]["selected_embedding_pattern"]["id"], embedding["id"])
        self.assertIn("Dimension limits: 2 static inputs", caller.complete.call_args_list[0].args[0])

    def test_static_data_spec_cannot_freeze_a_promoted_or_previously_added_input(self):
        parent = static_parent()
        child = child_with_freedom(parent, "parameter_to_input")
        spec = data_spec(child)
        spec_agent._validate_emitted_spec(spec, record=child)
        spec.independent_variables.pop()
        spec.parameters.append(spec_agent.FixedParam(symbol="a", value=1.0))
        for decision in ("parameter_to_input", "none"):
            child["evolution_contract"]["freedom_change"] = decision
            with self.subTest(decision=decision), self.assertRaisesRegex(ValueError, "evolved V inputs"):
                spec_agent._validate_emitted_spec(spec, record=child)

    def test_static_and_ode_promotions_produce_numeric_data_with_released_quantity(self):
        child = validate(static_parent(), child_with_freedom(static_parent(), "parameter_to_input"))
        spec = data_spec(child)
        spec_agent._validate_emitted_spec(spec, record=child)
        columns, values = gen_evaluate_explicit(spec.model_dump() | {"_n_total": 5000, "noise": 0.5}, seed=4)
        self.assertEqual(columns, ["x", "a", "y"])
        self.assertEqual(values.shape, (5000, 3))
        self.assertGreater(np.ptp(values[:, 1]), 1.0)
        np.testing.assert_allclose(values[:, 2], values[:, 0] * values[:, 1])

        child = validate(ode_parent(), child_with_freedom(ode_parent(), "parameter_to_state"))
        spec = data_spec(child)
        spec_agent._validate_emitted_spec(spec, ode_contract=spec_agent._ode_contract(child), record=child)
        generated = spec_agent.attach_ode_benchmark_metadata(spec.model_dump(), child)
        columns, values = gen_integrate_system(generated | {"_n_total": 5000, "noise": 0.5}, seed=4)
        self.assertEqual(values.shape[0], 5000)
        self.assertFalse(any(name.endswith("_noisy") for name in columns))
        self.assertTrue(np.isfinite(values).all())
        self.assertGreater(np.ptp(values[:, columns.index("r")]), 0.1)
        np.testing.assert_allclose(values[:, columns.index("dN")],
                                   values[:, columns.index("r")] * values[:, columns.index("N")])


    def test_data_spec_emits_clean_plan_with_parent_without_excitation(self):
        parent = static_parent()
        child = child_with_freedom(parent, "parameter_to_input")
        spec = data_spec(child).model_dump()
        spec.update(noise=0.5, excitation_ok=False, excitation_report="legacy fields")
        calls = [
            ("analyze_expression", {"expression": child["expression"], "target_symbol": "y"}),
            ("emit_data_gen_spec", spec),
        ]
        caller = Mock()
        caller.chat.return_value = {"choices": [{"message": {"tool_calls": [
            {"id": str(index), "function": {"name": name, "arguments": json.dumps(args)}}
            for index, (name, args) in enumerate(calls)
        ]}}]}
        with patch.object(spec_agent, "build_model_caller", return_value=caller):
            result = spec_agent.plan_data_generation_openrouter(
                child, "science", model="offline", parent=parent, max_turns=1, verbose=False,
            )
        self.assertEqual([axis["symbol"] for axis in result["independent_variables"]], ["x", "a"])
        self.assertEqual(result["noise"], 0)
        self.assertNotIn("excitation_ok", result)
        self.assertNotIn("excitation_report", result)
        self.assertEqual([item["tool"] for item in result["_trace"] if "tool" in item],
                         ["analyze_expression", "emit_data_gen_spec"])
        self.assertEqual(caller.chat.call_count, 1)

    def test_anthropic_spec_tools_emit_clean_plan_without_excitation(self):
        parent = static_parent()
        child = child_with_freedom(parent, "parameter_to_input")
        emitted = data_spec(child).model_dump() | {"noise": 0.5}
        registered = {}

        def fake_tool(name, description, schema):
            def decorate(func):
                registered[name] = func
                return func
            return decorate

        async def fake_query(**kwargs):
            await registered["emit_data_gen_spec"](emitted)
            if False:
                yield None

        with patch.object(spec_agent, "_SDK_IMPORT_ERROR", None), \
                patch.object(spec_agent, "tool", side_effect=fake_tool), \
                patch.object(spec_agent, "create_sdk_mcp_server", return_value=object()), \
                patch.object(spec_agent, "ClaudeAgentOptions", side_effect=lambda **kw: SimpleNamespace(**kw)), \
                patch.object(spec_agent, "anthropic_runtime_env", return_value={}), \
                patch.object(spec_agent, "query", fake_query):
            result = asyncio.run(spec_agent.plan_data_generation_async(
                child, "science", parent=parent, model="offline", verbose=False,
            ))
        self.assertEqual(set(registered), {"analyze_expression", "check_substitution", "emit_data_gen_spec"})
        self.assertEqual(result["noise"], 0)
        self.assertEqual([axis["symbol"] for axis in result["independent_variables"]], ["x", "a"])



if __name__ == "__main__":
    unittest.main()
