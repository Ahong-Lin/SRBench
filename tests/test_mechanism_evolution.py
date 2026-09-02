import random
import sys
import unittest
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import equation_evolve as evolve
from mechanism_ontology import load_taxonomy_profile, validate_contract_fields
from quality.observable_gate import assess_observable_variation


def _profile():
    return load_taxonomy_profile("physics", "classical_mechanics")


def _current():
    return {
        "model_family": "static", "equation_type": "static_explicit",
        "target_symbol": "y", "expression": "a*x",
        "symbols": ["y", "x", "a"],
        "symbol_descriptions": ["output", "input", "coefficient"],
        "symbol_properties": ["O", "V", "P"],
    }


def _contract(operation="add_term", mechanism_id="nonlinear_drag"):
    return {
        "operation": operation, "scope_kind": "pairwise", "scope_symbols": ["x", "y"],
        "structural_role": "response_law", "domain_mechanism_id": mechanism_id,
        "domain_mechanism": "velocity-dependent nonlinear response",
        "scientific_mechanism": "velocity-dependent nonlinear response",
        "embedding_pattern": "state_coupling",
        "difficulty_rationale": "joint dependence cannot be represented by a coefficient-only correction",
        "assumption_before": "linear response", "assumption_after": "nonlinear response",
        "before_fragment": "a*x", "after_fragment": "a*x + b*x**2",
        "parent_reduction": "b -> 0", "observable_signature": "curvature changes with x",
        "shortcut_blocked": "a coefficient cannot reproduce curvature over the full range",
    }


class MechanismEvolutionTests(unittest.TestCase):
  def test_add_term_contract_requires_declared_scope_but_not_profile_whitelist(self):
    profile = _profile()
    with self.assertRaises(ValueError):
        validate_contract_fields(_contract() | {"scope_symbols": ["x", "z"]}, profile, {"y", "x"})
    good = _contract(mechanism_id="nonlinear_drag")
    # A profile-known mechanism remains valid, but a new scientific mechanism
    # may now be recorded provisionally rather than being rejected by name.
    validate_contract_fields(good, profile, {"y", "x", "a", "b"})
    provisional = _contract(mechanism_id="new_domain_mechanism") | {
        "domain_mechanism": "new scenario-natural mechanism",
        "scientific_mechanism": "new scenario-natural mechanism",
        "taxonomy_match": "provisional",
    }
    validate_contract_fields(provisional, profile, {"y", "x", "a", "b"})

  def test_embedding_draw_is_seed_reproducible_and_compatible(self):
    current = _current()
    first = evolve.sample_embedding_pattern(random.Random(12), current, "add_term")
    second = evolve.sample_embedding_pattern(random.Random(12), current, "add_term")
    self.assertEqual(first["id"], second["id"])
    self.assertNotEqual(first["id"], "auxiliary_state_feedback")

  def test_contract_requires_new_mechanism_and_embedding_fields(self):
    profile = _profile()
    for field in ("scientific_mechanism", "embedding_pattern", "difficulty_rationale"):
        bad = _contract()
        bad[field] = ""
        with self.assertRaises(ValueError):
            validate_contract_fields(bad, profile, {"y", "x", "a", "b"})


  def test_add_term_cannot_add_a_v_input(self):
    child = _current() | {
        "expression": "a*x + b*z", "symbols": ["y", "x", "a", "b", "z"],
        "symbol_descriptions": ["output", "input", "coefficient", "coefficient", "new input"],
        "symbol_properties": ["O", "V", "P", "P", "V"],
        "new_symbol_range_suggestions": {"b": "[0,1]", "z": "[0,1]"},
        "assumption_audit": None, "add_term_audit": {
            "mechanism_class": "interaction", "mechanism_claim": "new interaction",
            "parent_reduction": "b -> 0", "observable_signature": "interaction curvature",
        }, "evolution_contract": _contract() | {"after_fragment": "a*x + b*z"},
    }
    with self.assertRaisesRegex(evolve.EvolvedEquationValidationError, "V inputs"):
        evolve._normalize_and_validate_evolved(
            _current(), child, "add_term", "extended", 4, 4,
            mechanism_profile=_profile(),
        )


  def test_fixed_univariate_rejects_condition_promotion(self):
    current = _current()
    child = current | {
        "expression": "a*x + b*T", "symbols": ["y", "x", "a", "b", "T"],
        "symbol_descriptions": ["output", "input", "coefficient", "coefficient", "condition"],
        "symbol_properties": ["O", "V", "P", "P", "V"],
        "new_symbol_range_suggestions": {"b": "[0,1]", "T": "[0,1]"},
        "assumption_audit": {
            "released_assumption": "fixed temperature", "outcome": "condition_promotion",
            "quantity": "T", "quantity_role": "controlled_input", "mechanism": "thermal",
            "reference_condition": {"T": 0.0}, "parent_reduction": "T=0",
        }, "add_term_audit": None,
        "evolution_contract": _contract("change_assumption", "thermal_friction") | {
            "scope_kind": "unary", "scope_symbols": ["T"], "structural_role": "modulation",
            "domain_mechanism": "thermal friction", "after_fragment": "a*x + b*T",
        },
    }
    with self.assertRaisesRegex(evolve.EvolvedEquationValidationError, "fixed_univariate"):
        evolve._normalize_and_validate_evolved(
            current, child, "change_assumption", "extended", 4, 4,
            mechanism_profile=_profile(), dimension_track="fixed_univariate",
        )


  def test_legacy_record_can_be_recorded_without_contract(self):
    rec = evolve._record(_current(), "demo", 0, "base", "demo scenario")
    self.assertIsNone(rec["evolution_contract"])
    self.assertEqual(rec["dimension_track"], "fixed_univariate")

  def test_contract_fragments_must_match_parent_and_child(self):
    child = _current() | {
        "expression": "a*x + b*x**2", "symbols": ["y", "x", "a", "b"],
        "symbol_descriptions": ["output", "input", "coefficient", "coefficient"],
        "symbol_properties": ["O", "V", "P", "P"],
        "new_symbol_range_suggestions": {"b": "[0,1]"},
        "assumption_audit": None, "add_term_audit": {
            "mechanism_class": "nonlinear_response", "mechanism_claim": "nonlinear drag",
            "parent_reduction": "b -> 0", "observable_signature": "curvature",
        }, "evolution_contract": _contract() | {"before_fragment": "not_in_parent"},
    }
    with self.assertRaisesRegex(evolve.EvolvedEquationValidationError, "before_fragment"):
        evolve._normalize_and_validate_evolved(
            _current(), child, "add_term", "extended", 4, 4,
            mechanism_profile=_profile(),
        )

  def test_observable_gate_does_not_reject_static_saturation(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / "constant.csv"
      path.write_text("x,y\n0,0\n1,1\n2,1.9\n", encoding="utf-8")
      report = assess_observable_variation(
          {"integrator": "evaluate_explicit", "benchmark_output": "y"}, [path]
      )
      self.assertTrue(report["accepted"])

  def test_observable_gate_rejects_terminally_converged_ode(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / "ode.csv"
      rows = ["t,y"]
      rows.extend(f"{i},{1.0 - 0.8 * (0.5 ** i)}" for i in range(20))
      path.write_text("\n".join(rows) + "\n", encoding="utf-8")
      report = assess_observable_variation(
          {"integrator": "integrate_ode", "benchmark_output": "y"}, [path],
          terminal_window_fraction=0.2,
      )
      self.assertFalse(report["accepted"])
      self.assertIn("numerical_terminal_convergence", report["reasons"])
      convergence = report["ode_convergence"][0]
      self.assertLess(convergence["r1_terminal_range_ratio"], 0.02)
      self.assertLess(convergence["r2_terminal_median_shift_ratio"], 0.02)

  def test_observable_gate_accepts_nonconvergent_ode(self):
    with tempfile.TemporaryDirectory() as tmp:
      path = Path(tmp) / "ode.csv"
      rows = ["t,y"]
      rows.extend(f"{i},{(-1.0) ** i}" for i in range(40))
      path.write_text("\n".join(rows) + "\n", encoding="utf-8")
      report = assess_observable_variation(
          {"integrator": "integrate_ode", "benchmark_output": "y"}, [path]
      )
      self.assertTrue(report["accepted"])


if __name__ == "__main__":
    unittest.main()
