"""
Equation Evolution: take a base equation and make it progressively richer.
===========================================================================

Feed in ONE equation produced by `auto_workflow.py` (Stage 3 output) and this
script evolves it step by step. At each step it flips a coin (50/50 by default)
and asks the LLM to do ONE of two things:

  (1) change_assumption — pick a variable/parameter, RELAX or CHANGE the
      physical assumption originally made about it, then RE-DERIVE the equation
      under the new assumption.
  (2) add_term — ADD one new function term that introduces a fresh physical
      effect (damping, forcing, coupling, nonlinearity, saturation, ...), making
      the model background more complex.

The output of each step becomes the input to the next, so the formula keeps
growing in complexity. Static relations remain static relations. ODE systems
remain closed ODE systems: their time axis, states, state RHS expressions, and
initial conditions are carried through every generation.

Usage
-----
    export ANTHROPIC_API_KEY="sk-..."

    # Evolve the first equation in a run's equations.jsonl for 5 steps:
    python equation_evolve.py \
        --input outputs/physics_20260529-2359/equations.jsonl \
        --steps 5

    # Pick a specific equation by its scenario_id:
    python equation_evolve.py \
        --input outputs/physics_.../equations.jsonl \
        --id m2_classical_mechanics_0_000 \
        --steps 8 --seed 42

    # Bias the coin toward adding terms (70% add, 30% assumption-change):
    python equation_evolve.py --input eq.jsonl --steps 6 --p-assumption 0.3
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

from model_provider import ModelCaller, ModelRequestError, build_model_caller


# novelty_check.py lives next to this file.
NOVELTY_CHECK = Path(__file__).resolve().parent / "novelty_check.py"


def _load_module(label: str, path: Path):
    if not path.exists():
        raise SystemExit(f"Cannot find '{label}' module at:\n  {path}")
    import importlib.util

    spec = importlib.util.spec_from_file_location(f"_pse_{label}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"_pse_{label}"] = module
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def _strip_code_fence(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1:]
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


# ============================================================
# Output schema — same fields as EquationOutput + change_summary
# ============================================================

ModelFamily = Literal["static", "ode"]
EquationType = Literal["static_explicit", "static_implicit", "ode_system"]
AssumptionMode = Literal["core", "extended"]

MAX_STATIC_INPUTS_DEFAULT = 4
MAX_ODE_STATES_DEFAULT = 4


class AssumptionAudit(BaseModel):
    """Scientific consequence of one assumption-relaxation operation."""

    released_assumption: str
    outcome: Literal[
        "law_refinement",
        "parameter_refinement",
        "boundary_change",
        "regime_change",
        "condition_promotion",
        "state_augmentation",
    ]
    quantity: Optional[str] = None
    quantity_role: Literal[
        "controlled_input",
        "observed_covariate",
        "internal_state",
        "fixed_parameter",
        "not_applicable",
    ]
    mechanism: str
    reference_condition: dict[str, float] = Field(default_factory=dict)
    parent_reduction: str = ""


class ODEStateEquation(BaseModel):
    symbol: str
    rhs: str
    initial_condition: float
    description: str


class ODESystem(BaseModel):
    time_symbol: str
    target_state: str
    states: list[ODEStateEquation] = Field(min_length=1)


class EvolvedEquation(BaseModel):
    model_family: ModelFamily
    equation_type: EquationType
    target_symbol: str
    expression: str
    symbols: list[str]
    symbol_descriptions: list[str]
    symbol_properties: list[str]
    new_symbol_range_suggestions: dict[str, str]
    derivation_notes: str
    change_summary: str
    assumption_audit: Optional[AssumptionAudit] = None
    ode_system: Optional[ODESystem] = None


class EvolvedEquationValidationError(ValueError):
    """Raised when an evolved equation is structurally inconsistent."""


# ============================================================
# Prompts
# ============================================================

_HEADER = """\
You are an expert in {discipline} performing mathematical modeling for a
symbolic-regression benchmark. You are given a CURRENT governing equation and
must produce a MORE COMPLEX successor equation.

ORIGINAL PHENOMENON CONTEXT:
{scenario_text}

CURRENT EQUATION:
  {target_symbol} = {expression}

CURRENT SYMBOLS (symbol [role] — description):
{symbol_table}

MODEL FAMILY: {model_family}
EQUATION TYPE: {equation_type}
{system_block}
"""

_COMMON_RULES = """
GENERAL REQUIREMENTS:
1. Write every RHS in Python/sympy syntax: **, sqrt(), sin(), cos(), exp(), log(),
   Abs(), tanh(), etc. Use descriptive parameter names. Do not use floating-point
   literals for physical constants.
2. Keep the same model_family and equation_type as the current model. Declare every
   symbol used, preserve existing symbols unless the scientific re-derivation truly
   removes a mechanism, and give a range suggestion for every NEW symbol.
3. symbol_properties distinguishes mathematical roles:
   - O: the target output or target derivative;
   - V: a static independently sampled input, or the ONE ODE time axis only;
   - S: an ODE internal state, which changes along the time trajectory and is never
        independently sampled;
   - P: a fixed parameter for one generated dataset.
"""

_STATIC_RULES = """
STATIC MODEL RULES:
- expression is the RHS for static_explicit, or the complete g(...)=0 expression
  for static_implicit.
- V symbols are exactly the independently sampled inputs. S is not allowed.
- Do not introduce time derivatives, initial conditions, or an ode_system.
"""

_ODE_RULES = """
ODE SYSTEM RULES:
- expression is exactly the RHS of the target_state equation.
- ode_system must repeat the same time_symbol and target_state and include every
  state with one local first-order RHS and one finite initial_condition.
- States use S, only the time axis uses V, and parameters use P.
- Every state RHS may reference only the time symbol, declared states, fixed
  parameters, and standard math functions. Do not use x(t), Derivative, Integral,
  delay/history terms, PDE terms, or an ungoverned h(t).
"""

_OUTPUT_SCHEMA = """
OUTPUT FORMAT — return a SINGLE JSON object, nothing else:
{{
  "model_family": "{model_family}",
  "equation_type": "{equation_type}",
  "target_symbol": "{target_symbol}",
  "expression": "<sympy expression string>",
  "symbols": ["<target>", "<variable/state>", "<parameter>", ...],
  "symbol_descriptions": ["<desc>", "<desc>", ...],
  "symbol_properties": ["O", "V" or "S", "P", ...],
  "new_symbol_range_suggestions": {{"<new_symbol>": "<suggested range>", ...}},
  "derivation_notes": "<1-2 sentences on the physical mechanism>",
  "change_summary": "<1-2 sentences on what changed and why>",
  "assumption_audit": {assumption_audit_schema},
  "ode_system": {ode_system_schema}
}}
The first character of your response must be `{{` and the last must be `}}`.
Do NOT wrap in markdown fences. Do NOT add any prose before or after the JSON.
"""

CHANGE_ASSUMPTION_PROMPT = _HEADER + """
YOUR TASK — CHANGE AN ASSUMPTION:
First, REASON ABOUT THIS SPECIFIC SYSTEM. Looking at the phenomenon context and
the current equation above, identify which simplifying assumption is the most
physically questionable or restrictive FOR THIS PARTICULAR MODEL — i.e. the
idealization a domain expert would most want to drop next when moving from a
textbook treatment toward a realistic description of THIS system.

Then pick exactly ONE variable or parameter and RELAX or CHANGE that assumption,
and RE-DERIVE the governing equation under the new assumption. The change must be
physically motivated by THIS system's mechanism, not a generic substitution.

Classify the scientific consequence as exactly one assumption_audit.outcome:
  - law_refinement: an existing law/property becomes more realistic without
    changing observed inputs or ODE states;
  - parameter_refinement: a fixed parameter is refined but remains fixed;
  - boundary_change: a boundary/geometry idealization is relaxed without adding
    an observed input or ODE state;
  - regime_change: a single-regime approximation is relaxed without adding an
    observed input or ODE state;
  - condition_promotion: STATIC ONLY. A formerly fixed external condition becomes
    one new independently controllable/measured V input. State the numeric
    reference_condition and how the successor reduces to the parent there;
  - state_augmentation: ODE ONLY. A formerly quasi-steady or omitted internal
    quantity becomes one new S state. Add its RHS and initial condition, explain
    the parent_reduction (e.g. fast relaxation or fixed-state limit), and make the
    full ODE system closed.

Do not use condition_promotion or state_augmentation merely to make the equation
higher-dimensional. The successor must be a natural next refinement for this
specific phenomenon.

"""

ADD_TERM_PROMPT = _HEADER + """
YOUR TASK — ADD A FUNCTION TERM:
First, REASON ABOUT THIS SPECIFIC SYSTEM. Looking at the phenomenon context and
the current equation above, identify which real physical effect is currently
MISSING from this model and would be the most natural, physically-motivated
next complication to include FOR THIS PARTICULAR SYSTEM. The new term must arise
from the actual mechanism of THIS phenomenon — not be a generic term bolted on.

Then ADD exactly ONE new function term that captures that effect. Keep the
existing structure and incorporate the new term; do not simplify away what is
already there. The successor equation must be richer and more complex.

The new term may add fixed parameters, but it MUST NOT add a V input or S state,
change the model family/type, alter the time axis, or alter initial conditions.
For an ODE system, preserve the full state set and add the mechanism to the
appropriate existing state RHS expression. Set assumption_audit to null.

"""


# ============================================================
# Helpers
# ============================================================

def _role_name(letter: str) -> str:
    return {
        "O": "output/target derivative",
        "V": "independently sampled input or time axis",
        "S": "internally evolved state",
        "P": "fixed parameter",
    }.get(letter, "?")


_IDENTIFIER_RE = re.compile(r"\b[A-Za-z_]\w*\b")
_CALLED_NAME_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_SYMPY_CALLS = {
    "Abs", "Max", "Min", "Piecewise", "Heaviside",
    "sin", "cos", "tan", "asin", "acos", "atan",
    "sinh", "cosh", "tanh", "exp", "log", "sqrt",
    "sign", "floor", "ceiling",
}
_SYMPY_NAMES = _SYMPY_CALLS | {"pi", "E", "I", "oo", "nan", "True", "False"}


def _extract_expression_names(
    expression: str,
    declared_symbols: set[str] | None = None,
) -> tuple[set[str], set[str]]:
    """Collect expression names, respecting declared symbols that shadow SymPy constants."""
    names = set(_IDENTIFIER_RE.findall(expression))
    called = set(_CALLED_NAME_RE.findall(expression))
    custom_called = {name for name in called if name not in _SYMPY_CALLS}
    used = {name for name in names if name not in _SYMPY_NAMES}
    # Benchmark equations can legitimately use `I` for electric current or `E`
    # for energy. Treat a reserved SymPy singleton as a variable when the model
    # explicitly declares it in this candidate equation.
    if declared_symbols:
        used |= names & declared_symbols
    return used, custom_called


def _model_family(eq: dict) -> ModelFamily:
    """Read new metadata, treating pre-metadata records as legacy static models."""
    family = eq.get("model_family") or "static"
    if family not in {"static", "ode"}:
        raise EvolvedEquationValidationError(f"unknown model_family '{family}'")
    return family


def _normalize_base_equation(record: dict) -> dict:
    """Give legacy Stage-3 records conservative static metadata for evolution."""
    base = dict(record)
    family = _model_family(base)
    base["model_family"] = family
    expected_type = "ode_system" if family == "ode" else "static_explicit"
    equation_type = base.get("equation_type") or expected_type
    if family == "static" and equation_type not in {"static_explicit", "static_implicit"}:
        raise EvolvedEquationValidationError(
            "static base equation must use static_explicit or static_implicit"
        )
    if family == "ode" and equation_type != "ode_system":
        raise EvolvedEquationValidationError("ODE base equation must use ode_system")
    base["equation_type"] = equation_type
    if family == "static":
        base["ode_system"] = None
    elif not base.get("ode_system"):
        raise EvolvedEquationValidationError(
            "ODE base equation is missing ode_system; it cannot be evolved safely"
        )
    return base


def _symbol_roles(eq: dict) -> dict[str, str]:
    symbols = list(eq.get("symbols") or [])
    roles = list(eq.get("symbol_properties") or [])
    if len(symbols) != len(roles):
        raise EvolvedEquationValidationError(
            "symbols and symbol_properties must have the same length"
        )
    return dict(zip(symbols, roles))


def _ode_states(eq: dict) -> list[dict]:
    ode = eq.get("ode_system") or {}
    states = ode.get("states") if isinstance(ode, dict) else None
    if not isinstance(states, list):
        raise EvolvedEquationValidationError("ODE equation must include ode_system.states")
    return states


def _require_finite_mapping(values: dict[str, float], label: str) -> None:
    for key, value in values.items():
        if not math.isfinite(value):
            raise EvolvedEquationValidationError(
                f"{label} value for '{key}' must be finite"
            )


def _validate_ode_structure(
    out: dict,
    max_ode_states: int,
) -> dict[str, object]:
    """Validate a closed first-order state system and return its role metadata."""
    ode = out.get("ode_system")
    if not isinstance(ode, dict):
        raise EvolvedEquationValidationError("ODE equation requires an ode_system object")
    time_symbol = ode.get("time_symbol")
    target_state = ode.get("target_state")
    states = _ode_states(out)
    if not isinstance(time_symbol, str) or not time_symbol:
        raise EvolvedEquationValidationError("ode_system.time_symbol is required")
    if not isinstance(target_state, str) or not target_state:
        raise EvolvedEquationValidationError("ode_system.target_state is required")
    if not 1 <= len(states) <= max_ode_states:
        raise EvolvedEquationValidationError(
            f"ODE systems must contain 1-{max_ode_states} states"
        )

    state_names = [state.get("symbol") for state in states]
    if any(not isinstance(name, str) or not name for name in state_names):
        raise EvolvedEquationValidationError("every ODE state needs a non-empty symbol")
    if len(set(state_names)) != len(state_names):
        raise EvolvedEquationValidationError("ode_system state symbols must be distinct")
    if target_state not in state_names:
        raise EvolvedEquationValidationError("ode_system.target_state must be a declared state")

    roles = _symbol_roles(out)
    symbols = set(roles)
    target_symbol = out.get("target_symbol")
    if roles.get(target_symbol) != "O":
        raise EvolvedEquationValidationError("target_symbol must have O role")
    if roles.get(time_symbol) != "V":
        raise EvolvedEquationValidationError("ODE time_symbol must have V role")
    v_symbols = {symbol for symbol, role in roles.items() if role == "V"}
    if v_symbols != {time_symbol}:
        raise EvolvedEquationValidationError(
            "ODE V symbols must contain only ode_system.time_symbol"
        )
    state_set = set(state_names)
    s_symbols = {symbol for symbol, role in roles.items() if role == "S"}
    if s_symbols != state_set:
        raise EvolvedEquationValidationError(
            "ODE S symbols must exactly match ode_system states; got "
            f"{sorted(s_symbols)}, expected {sorted(state_set)}"
        )
    if target_symbol not in symbols or time_symbol not in symbols:
        raise EvolvedEquationValidationError("ODE target and time symbols must be declared")

    parameters = {symbol for symbol, role in roles.items() if role == "P"}
    allowed = state_set | {time_symbol} | parameters
    target_rhs = None
    used_anywhere: set[str] = set()
    for state in states:
        symbol = state["symbol"]
        rhs = (state.get("rhs") or "").strip()
        if not rhs:
            raise EvolvedEquationValidationError(f"state '{symbol}' has an empty RHS")
        initial_condition = state.get("initial_condition")
        if not isinstance(initial_condition, (int, float)) or not math.isfinite(initial_condition):
            raise EvolvedEquationValidationError(
                f"state '{symbol}' must have a finite numeric initial_condition"
            )
        if not str(state.get("description") or "").strip():
            raise EvolvedEquationValidationError(f"state '{symbol}' needs a description")
        if "Derivative" in rhs or "Integral" in rhs:
            raise EvolvedEquationValidationError(
                f"state '{symbol}' RHS must be local and first-order"
            )
        names, custom_calls = _extract_expression_names(rhs, symbols)
        if custom_calls:
            raise EvolvedEquationValidationError(
                f"state '{symbol}' RHS contains ungoverned calls: "
                + ", ".join(sorted(custom_calls))
            )
        unknown = sorted(names - allowed)
        if unknown:
            raise EvolvedEquationValidationError(
                f"state '{symbol}' RHS uses undeclared/non-state symbols: "
                + ", ".join(unknown)
            )
        used_anywhere |= names
        if symbol == target_state:
            target_rhs = rhs

    if target_rhs != out.get("expression"):
        raise EvolvedEquationValidationError(
            "expression must exactly equal the target state's RHS"
        )
    # A state is defined by the left-hand side of its own ODE, even when it is a
    # pure accumulator and therefore never appears on a RHS.  Classical SIR's
    # recovered compartment is the canonical example: dR/dt = gamma*I.  Count
    # declared state symbols as used, while retaining the check for genuinely
    # unused parameters or other symbols.
    used_anywhere |= state_set
    unused = sorted(
        symbol for symbol in symbols
        if symbol not in {target_symbol, time_symbol} and symbol not in used_anywhere
    )
    if unused:
        raise EvolvedEquationValidationError(
            "ODE symbols declared but unused by every state RHS: " + ", ".join(unused)
        )
    return {
        "time_symbol": time_symbol,
        "target_state": target_state,
        "states": state_set,
        "state_records": {state["symbol"]: state for state in states},
        "parameters": parameters,
    }


def _normalize_and_validate_evolved(
    current: dict,
    candidate: dict,
    operation: str,
    assumption_mode: AssumptionMode,
    max_static_inputs: int,
    max_ode_states: int,
) -> tuple[dict, list[str]]:
    """Validate type, closure, dimensions, and operation-specific invariants."""
    current = _normalize_base_equation(current)
    out = dict(candidate)
    target_symbol = current.get("target_symbol", "")

    if out.get("target_symbol") != target_symbol:
        raise EvolvedEquationValidationError(
            f"target_symbol changed from '{target_symbol}' to "
            f"'{out.get('target_symbol')}'. Keep the same target."
        )

    expression = (out.get("expression") or "").strip()
    if not expression:
        raise EvolvedEquationValidationError("expression is empty")

    symbols = list(out.get("symbols") or [])
    descriptions = list(out.get("symbol_descriptions") or [])
    properties = list(out.get("symbol_properties") or [])
    if not symbols:
        raise EvolvedEquationValidationError("symbols is empty")
    if len(symbols) != len(descriptions) or len(symbols) != len(properties):
        raise EvolvedEquationValidationError(
            "symbols / symbol_descriptions / symbol_properties must have the same length"
        )
    if len(set(symbols)) != len(symbols):
        raise EvolvedEquationValidationError("symbols contains duplicates")

    invalid_roles = [p for p in properties if p not in {"O", "V", "S", "P"}]
    if invalid_roles:
        raise EvolvedEquationValidationError(
            f"invalid symbol_properties found: {sorted(set(invalid_roles))}"
        )

    o_symbols = [sym for sym, prop in zip(symbols, properties) if prop == "O"]
    if o_symbols != [target_symbol]:
        raise EvolvedEquationValidationError(
            f"exactly one 'O' is required and it must be '{target_symbol}', got {o_symbols}"
        )

    family = _model_family(current)
    if out.get("model_family") != family:
        raise EvolvedEquationValidationError("model_family must remain unchanged")
    if out.get("equation_type") != current.get("equation_type"):
        raise EvolvedEquationValidationError("equation_type must remain unchanged")

    roles = _symbol_roles(out)
    declared = set(symbols)
    if family == "static":
        if out.get("ode_system") is not None:
            raise EvolvedEquationValidationError("static equations cannot contain ode_system")
        if "S" in roles.values():
            raise EvolvedEquationValidationError("static equations cannot use S states")
        used_names, custom_called = _extract_expression_names(expression, declared)
        if custom_called:
            raise EvolvedEquationValidationError(
                "expression contains ungoverned function calls: "
                + ", ".join(sorted(custom_called))
            )
        unknown = sorted(used_names - declared)
        if unknown:
            raise EvolvedEquationValidationError(
                "expression uses undeclared symbols: " + ", ".join(unknown)
            )
        unused = sorted(
            sym for sym in symbols if sym != target_symbol and sym not in used_names
        )
        if unused:
            raise EvolvedEquationValidationError(
                "symbols declared but not used in expression: " + ", ".join(unused)
            )
        v_symbols = {symbol for symbol, role in roles.items() if role == "V"}
        if not 1 <= len(v_symbols) <= max_static_inputs:
            raise EvolvedEquationValidationError(
                f"static equations must have 1-{max_static_inputs} V inputs"
            )
        ode_info: dict[str, object] | None = None
    else:
        if out.get("equation_type") != "ode_system":
            raise EvolvedEquationValidationError("ODE models must use equation_type='ode_system'")
        ode_info = _validate_ode_structure(out, max_ode_states)
        v_symbols = {ode_info["time_symbol"]}

    current_symbols = set(current.get("symbols", []))
    new_symbols = [sym for sym in symbols if sym not in current_symbols and sym != target_symbol]
    range_suggestions = dict(out.get("new_symbol_range_suggestions") or {})
    unexpected = sorted(sym for sym in range_suggestions if sym not in new_symbols)
    if unexpected:
        raise EvolvedEquationValidationError(
            "new_symbol_range_suggestions contains non-new symbols: " +
            ", ".join(unexpected)
        )
    missing_ranges = sorted(
        sym for sym in new_symbols if not str(range_suggestions.get(sym, "")).strip()
    )
    if missing_ranges:
        raise EvolvedEquationValidationError(
            "missing suggested range for new symbols: " + ", ".join(missing_ranges)
        )

    current_roles = _symbol_roles(current)
    current_v_symbols = {
        symbol for symbol, role in current_roles.items() if role == "V"
    }
    if operation not in {"change_assumption", "add_term"}:
        raise EvolvedEquationValidationError(f"unsupported evolution operation '{operation}'")

    audit = out.get("assumption_audit")
    if operation == "add_term":
        if audit is not None:
            raise EvolvedEquationValidationError("add_term must set assumption_audit to null")
        removed = sorted(set(current.get("symbols", [])) - set(symbols))
        if removed:
            raise EvolvedEquationValidationError(
                "add_term must preserve every existing symbol; removed "
                + ", ".join(removed)
            )
        if v_symbols != current_v_symbols:
            raise EvolvedEquationValidationError("add_term must not add/remove V inputs")
        if family == "ode":
            current_ode = _validate_ode_structure(current, max_ode_states)
            if ode_info is None:  # pragma: no cover - family guards this path
                raise EvolvedEquationValidationError("missing ODE metadata")
            if ode_info["time_symbol"] != current_ode["time_symbol"]:
                raise EvolvedEquationValidationError("add_term cannot change the ODE time axis")
            if ode_info["states"] != current_ode["states"]:
                raise EvolvedEquationValidationError("add_term cannot add/remove ODE states")
            for symbol in ode_info["states"]:
                before = current_ode["state_records"][symbol]["initial_condition"]
                after = ode_info["state_records"][symbol]["initial_condition"]
                if before != after:
                    raise EvolvedEquationValidationError(
                        "add_term cannot change ODE initial conditions"
                    )
    else:
        if not isinstance(audit, dict):
            raise EvolvedEquationValidationError(
                "change_assumption requires a structured assumption_audit"
            )
        outcome = audit.get("outcome")
        if assumption_mode == "core" and outcome in {
            "condition_promotion", "state_augmentation",
        }:
            raise EvolvedEquationValidationError(
                f"{outcome} requires --assumption-mode extended"
            )
        reference = audit.get("reference_condition") or {}
        if not isinstance(reference, dict):
            raise EvolvedEquationValidationError("reference_condition must be an object")
        _require_finite_mapping(reference, "reference_condition")
        quantity = audit.get("quantity")
        parent_reduction = str(audit.get("parent_reduction") or "").strip()
        if outcome == "condition_promotion":
            if family != "static":
                raise EvolvedEquationValidationError("condition_promotion is static-only")
            added = v_symbols - current_v_symbols
            if len(added) != 1 or current_v_symbols - v_symbols:
                raise EvolvedEquationValidationError(
                    "condition_promotion must add exactly one V input"
                )
            promoted = next(iter(added))
            if quantity != promoted or audit.get("quantity_role") not in {
                "controlled_input", "observed_covariate",
            }:
                raise EvolvedEquationValidationError(
                    "condition_promotion audit must identify the new V quantity"
                )
            if promoted not in reference or not parent_reduction:
                raise EvolvedEquationValidationError(
                    "condition_promotion needs reference_condition and parent_reduction"
                )
        elif outcome == "state_augmentation":
            if family != "ode":
                raise EvolvedEquationValidationError("state_augmentation is ODE-only")
            current_ode = _validate_ode_structure(current, max_ode_states)
            if ode_info is None:  # pragma: no cover - family guards this path
                raise EvolvedEquationValidationError("missing ODE metadata")
            added = ode_info["states"] - current_ode["states"]
            if len(added) != 1 or current_ode["states"] - ode_info["states"]:
                raise EvolvedEquationValidationError(
                    "state_augmentation must add exactly one S state"
                )
            new_state = next(iter(added))
            if quantity != new_state or audit.get("quantity_role") != "internal_state":
                raise EvolvedEquationValidationError(
                    "state_augmentation audit must identify the new S state"
                )
            if not parent_reduction:
                raise EvolvedEquationValidationError(
                    "state_augmentation requires a parent_reduction explanation"
                )
            new_rhs = ode_info["state_records"][new_state]["rhs"]
            old_states = current_ode["states"]
            new_rhs_names, _ = _extract_expression_names(new_rhs, set(roles))
            if not new_rhs_names & old_states:
                raise EvolvedEquationValidationError(
                    "new state RHS must couple to an existing state"
                )
            old_rhs_names: set[str] = set()
            for symbol in old_states:
                names, _ = _extract_expression_names(
                    ode_info["state_records"][symbol]["rhs"], set(roles)
                )
                old_rhs_names |= names
            if new_state not in old_rhs_names:
                raise EvolvedEquationValidationError(
                    "an existing state RHS must couple back to the new state"
                )
        else:
            if outcome not in {
                "law_refinement", "parameter_refinement", "boundary_change", "regime_change",
            }:
                raise EvolvedEquationValidationError("unknown assumption_audit outcome")
            if v_symbols != current_v_symbols:
                raise EvolvedEquationValidationError(
                    f"{outcome} cannot add/remove V inputs"
                )
            if family == "ode":
                current_ode = _validate_ode_structure(current, max_ode_states)
                if ode_info is None or ode_info["states"] != current_ode["states"]:
                    raise EvolvedEquationValidationError(
                        f"{outcome} cannot add/remove ODE states"
                    )

    return out, []


def _symbol_table(eq: dict) -> str:
    rows = []
    syms = eq.get("symbols", [])
    descs = eq.get("symbol_descriptions", [])
    props = eq.get("symbol_properties", [])
    ranges = eq.get("new_symbol_range_suggestions", {})
    for i, sym in enumerate(syms):
        role = props[i] if i < len(props) else "?"
        desc = descs[i] if i < len(descs) else ""
        rng = ranges.get(sym, "")
        if rng:
            rows.append(f"  {sym} [{role}] — {desc} | suggested range: {rng}")
        else:
            rows.append(f"  {sym} [{role}] — {desc}")
    return "\n".join(rows) if rows else "  (none recorded)"


def _system_block(eq: dict) -> str:
    """Render the inherited system structure so the model cannot change it by accident."""
    if _model_family(eq) == "static":
        return "CURRENT SYSTEM STRUCTURE: static relation; no ODE system."
    ode = eq.get("ode_system") or {}
    return "CURRENT ODE SYSTEM (preserve unless state_augmentation is allowed):\n" + json.dumps(
        ode, ensure_ascii=False, indent=2
    )


def _output_schema_values(
    current: dict,
    operation: str,
) -> tuple[str, str]:
    """Return JSON snippets required by the operation and inherited model family."""
    if operation == "add_term":
        audit_schema = "null"
    else:
        audit_schema = """{
    "released_assumption": "<specific prior simplifying assumption>",
    "outcome": "law_refinement | parameter_refinement | boundary_change | regime_change | condition_promotion | state_augmentation",
    "quantity": "<affected symbol, or null when not applicable>",
    "quantity_role": "controlled_input | observed_covariate | internal_state | fixed_parameter | not_applicable",
    "mechanism": "<scientific mechanism justifying this refinement>",
    "reference_condition": {"<promoted input>": <finite reference value>},
    "parent_reduction": "<how the successor reduces to the parent; required for promotion/augmentation>"
  }"""
    if _model_family(current) == "static":
        return audit_schema, "null"
    return audit_schema, """{
    "time_symbol": "<same inherited time symbol>",
    "target_state": "<same inherited target state>",
    "states": [
      {"symbol": "<state>", "rhs": "<local first-order RHS>",
       "initial_condition": <finite number>, "description": "<state meaning>"}
    ]
  }"""


def _split_roles(eq: dict) -> dict:
    """Pull outputs, sampled inputs/time, states, and parameters from role labels."""
    syms = eq.get("symbols", [])
    descs = eq.get("symbol_descriptions", [])
    props = eq.get("symbol_properties", [])
    dependent, independent, states, parameters = None, [], [], []
    for i, sym in enumerate(syms):
        role = props[i] if i < len(props) else "?"
        desc = descs[i] if i < len(descs) else ""
        entry = {"symbol": sym, "description": desc}
        if role == "O":
            dependent = entry
        elif role == "V":
            independent.append(entry)
        elif role == "S":
            states.append(entry)
        elif role == "P":
            parameters.append(entry)
    return {
        "dependent_variable": dependent,
        "independent_variables": independent,
        "state_variables": states,
        "parameters": parameters,
    }


def _print_equation(eq: dict, prefix: str = "    ") -> None:
    roles = _split_roles(eq)
    dep = roles["dependent_variable"]
    indep = roles["independent_variables"]
    states = roles["state_variables"]
    params = roles["parameters"]
    print(f"{prefix}{eq.get('target_symbol','?')} = {eq.get('expression','?')}",
          file=sys.stderr)
    if dep:
        print(f"{prefix}  dependent  : {dep['symbol']} — {dep['description']}",
              file=sys.stderr)
    if indep:
        names = ", ".join(s["symbol"] for s in indep)
        label = "time axis" if eq.get("model_family") == "ode" else "inputs"
        print(f"{prefix}  {label:<11}: {names}", file=sys.stderr)
    if states:
        names = ", ".join(s["symbol"] for s in states)
        print(f"{prefix}  states      : {names}", file=sys.stderr)
    if params:
        names = ", ".join(s["symbol"] for s in params)
        print(f"{prefix}  parameters : {names}", file=sys.stderr)


# ============================================================
# Core: one evolution step
# ============================================================

def evolve_once(
    caller: ModelCaller,
    current: dict,
    operation: str,
    discipline: str,
    scenario_text: str,
    model: str,
    strip_fence,
    assumption_mode: AssumptionMode,
    max_static_inputs: int,
    max_ode_states: int,
    max_retries: int = 3,
    difficulty_feedback: str | None = None,
) -> dict:
    current = _normalize_base_equation(current)
    task_prompt = (
        CHANGE_ASSUMPTION_PROMPT
        if operation == "change_assumption"
        else ADD_TERM_PROMPT
    )
    family = _model_family(current)
    structure_rules = _STATIC_RULES if family == "static" else _ODE_RULES
    audit_schema, ode_schema = _output_schema_values(current, operation)
    template = task_prompt + _COMMON_RULES + structure_rules + _OUTPUT_SCHEMA
    assumption_mode_note = (
        "Only use law_refinement, parameter_refinement, boundary_change, or "
        "regime_change. Do not use condition_promotion or state_augmentation."
        if assumption_mode == "core"
        else "condition_promotion and state_augmentation are permitted only when "
        "scientifically justified by this specific system."
    )

    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            prompt = template.format(
                discipline=discipline,
                scenario_text=scenario_text or "(no scenario text recorded)",
                target_symbol=current.get("target_symbol", "y"),
                expression=current.get("expression", ""),
                symbol_table=_symbol_table(current),
                model_family=family,
                equation_type=current.get("equation_type"),
                system_block=_system_block(current),
                assumption_audit_schema=audit_schema,
                ode_system_schema=ode_schema,
            )
            if operation == "change_assumption":
                prompt += "\nASSUMPTION MODE: " + assumption_mode_note + "\n"
            if difficulty_feedback:
                prompt += (
                    "\nFINAL-BENCHMARK DIFFICULTY FEEDBACK FROM A REJECTED PRIOR LINEAGE:\n"
                    + difficulty_feedback.strip()
                    + "\nDo not merely add a small coefficient correction that a parent "
                    "can absorb. Make every immediate child structurally distinguishable "
                    "from its parent over a plausible experimental domain.\n"
                )
            if last_err is not None:
                prompt += (
                    "\nPREVIOUS ATTEMPT FAILED VALIDATION:\n"
                    f"{type(last_err).__name__}: {last_err}\n"
                    "Return a corrected JSON that keeps the same target symbol, "
                    "declares every symbol used in the expression, uses "
                    "symbol_properties consistently, and provides suggested "
                    "ranges for every newly introduced symbol.\n"
                )
            raw = caller.complete(prompt, model=model, max_tokens=4000)
            if not raw.strip():
                raise ValueError("empty response")
            parsed = json.loads(strip_fence(raw))
            validated = EvolvedEquation.model_validate(parsed)
            normalized, changes = _normalize_and_validate_evolved(
                current=current,
                candidate=validated.model_dump(),
                operation=operation,
                assumption_mode=assumption_mode,
                max_static_inputs=max_static_inputs,
                max_ode_states=max_ode_states,
            )
            if changes:
                print("      normalized symbol roles: " + "; ".join(changes),
                      file=sys.stderr, flush=True)
            return normalized
        except (
            ModelRequestError,
            json.JSONDecodeError,
            ValueError,
            EvolvedEquationValidationError,
        ) as e:
            last_err = e
            if attempt < max_retries:
                print(f"      retry {attempt+1}: {type(e).__name__}: {e}",
                      file=sys.stderr, flush=True)
                continue
            raise
    raise last_err  # pragma: no cover


def _record(eq: dict, base_id: str, generation: int, operation: str,
            scenario_text: str, novelty: dict | None = None) -> dict:
    """Assemble one lineage record with explicit variable roles."""
    rec = {
        "base_id": base_id,
        "generation": generation,
        "operation": operation,
        "model_family": eq.get("model_family", "static"),
        "equation_type": eq.get("equation_type", "static_explicit"),
        "target_symbol": eq.get("target_symbol", ""),
        "expression": eq.get("expression", ""),
        "symbols": eq.get("symbols", []),
        "symbol_descriptions": eq.get("symbol_descriptions", []),
        "symbol_properties": eq.get("symbol_properties", []),
        "new_symbol_range_suggestions": eq.get("new_symbol_range_suggestions", {}),
        "derivation_notes": eq.get("derivation_notes", ""),
        "change_summary": eq.get("change_summary", ""),
        "assumption_audit": eq.get("assumption_audit"),
        "ode_system": eq.get("ode_system"),
        "scenario_text": scenario_text,
    }
    rec.update(_split_roles(eq))
    if novelty is not None:
        rec["novelty"] = novelty
    return rec


# ============================================================
# Input loading
# ============================================================

def _load_usable_equations(input_path: Path) -> list[dict]:
    """Read all records that carry an 'expression' field, in file order."""
    if not input_path.exists():
        raise SystemExit(f"Input not found: {input_path}")

    records: list[dict] = []
    if input_path.suffix == ".jsonl":
        with input_path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    elif input_path.suffix == ".json":
        data = json.loads(input_path.read_text(encoding="utf-8"))
        records = data if isinstance(data, list) else [data]
    else:
        raise SystemExit(f"Unsupported input format: {input_path.suffix} (use .jsonl or .json)")

    usable = [r for r in records if r.get("expression")]
    if not usable:
        raise SystemExit(f"No records with an 'expression' field in {input_path}")
    return usable


def _eq_id(r: dict) -> str:
    return r.get("scenario_id") or r.get("id") or "equation"


def _format_catalog(usable: list[dict]) -> str:
    """One line per equation: index, id, subfield, target = expression preview."""
    lines = []
    width = len(str(len(usable) - 1))
    for i, r in enumerate(usable):
        eid = _eq_id(r)
        sub = r.get("subfield", "")
        sub = f" [{sub}]" if sub else ""
        target = r.get("target_symbol", "?")
        expr = r.get("expression", "")
        if len(expr) > 60:
            expr = expr[:57] + "..."
        lines.append(f"  [{i:>{width}}] {eid}{sub}\n        {target} = {expr}")
    return "\n".join(lines)


def _select_equation(usable: list[dict], want_id: str | None,
                     interactive: bool) -> dict:
    """Resolve which equation to evolve: explicit id > interactive prompt > first."""
    # 1) explicit --id (matches scenario_id or id)
    if want_id:
        for r in usable:
            if r.get("scenario_id") == want_id or r.get("id") == want_id:
                return r
        raise SystemExit(
            f"No equation with id '{want_id}'. Available ids:\n" +
            "\n".join(f"  - {_eq_id(r)}" for r in usable)
        )

    # 2) interactive picker — type an index or an id
    if interactive:
        print(f"\nEquations available in this file ({len(usable)}):",
              file=sys.stderr)
        print(_format_catalog(usable), file=sys.stderr)
        while True:
            try:
                raw = input(
                    f"\nSelect an equation to evolve "
                    f"(index 0-{len(usable)-1}, or paste an id; blank = 0): "
                ).strip()
            except EOFError:
                print("  (no input — defaulting to index 0)", file=sys.stderr)
                return usable[0]
            if raw == "":
                return usable[0]
            if raw.lstrip("-").isdigit():
                idx = int(raw)
                if 0 <= idx < len(usable):
                    return usable[idx]
                print(f"  index out of range (0-{len(usable)-1}); try again.",
                      file=sys.stderr)
                continue
            for r in usable:
                if r.get("scenario_id") == raw or r.get("id") == raw:
                    return r
            print("  no match for that id; try again.", file=sys.stderr)

    # 3) default: first usable equation
    return usable[0]


def _build_lineage_xlsx(out_path: Path, lineage: list[dict]) -> None:
    try:
        import pandas as pd
    except ImportError:
        print("    (pandas not available — skipping xlsx export)", file=sys.stderr)
        return
    rows = []
    for rec in lineage:
        indep = ", ".join(s["symbol"] for s in rec.get("independent_variables", []))
        states = ", ".join(s["symbol"] for s in rec.get("state_variables", []))
        params = ", ".join(s["symbol"] for s in rec.get("parameters", []))
        dep = rec.get("dependent_variable") or {}
        nov = rec.get("novelty") or {}
        rows.append({
            "generation": rec["generation"],
            "operation": rec["operation"],
            "model_family": rec.get("model_family", "static"),
            "equation_type": rec.get("equation_type", "static_explicit"),
            "target_symbol": rec["target_symbol"],
            "expression": rec["expression"],
            "dependent_variable": dep.get("symbol", ""),
            "independent_variables": indep,
            "state_variables": states,
            "parameters": params,
            "assumption_audit": json.dumps(
                rec.get("assumption_audit"), ensure_ascii=False
            ),
            "ode_system": json.dumps(rec.get("ode_system"), ensure_ascii=False),
            "new_symbol_range_suggestions": json.dumps(
                rec.get("new_symbol_range_suggestions", {}),
                ensure_ascii=False,
            ),
            "change_summary": rec["change_summary"],
            "derivation_notes": rec["derivation_notes"],
            "novel": nov.get("answer", ""),
            "novelty_reasoning": nov.get("reasoning", ""),
        })
    pd.DataFrame(rows).to_excel(out_path, index=False)


# ============================================================
# Main
# ============================================================

def main() -> None:
    p = argparse.ArgumentParser(
        description="Evolve a base equation into progressively more complex forms",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input", required=True,
                   help="equations.jsonl (or .json) from auto_workflow Stage 3")
    p.add_argument("--id", default=None,
                   help="scenario_id of the equation to evolve "
                        "(default: interactive picker, or first usable with --no-interactive)")
    p.add_argument("--list", action="store_true",
                   help="just list the equations in --input (index + id + expression) and exit")
    p.add_argument("--interactive", dest="interactive", action="store_true", default=True,
                   help="prompt for which equation to evolve when --id is not given (default: on)")
    p.add_argument("--no-interactive", dest="interactive", action="store_false",
                   help="disable the picker; fall back to the first usable equation")
    p.add_argument("--steps", type=int, default=5,
                   help="minimum evolution steps; also the generation at which "
                        "novelty checking begins (default: 5). With novelty off, "
                        "this is the exact number of steps.")
    p.add_argument("--max-steps", type=int, default=None,
                   help="hard cap on evolution steps when novelty gating keeps "
                        "requesting more (default: --steps + 10). Ignored when "
                        "novelty checking is off.")
    p.add_argument("--p-assumption", type=float, default=0.5,
                   help="probability of the 'change assumption' branch each step "
                        "(the rest go to 'add term')")
    p.add_argument("--assumption-mode", choices=["core", "extended"], default="extended",
                   help="core permits only non-dimensional assumption refinements; "
                        "extended also permits condition promotion and state augmentation")
    p.add_argument("--max-static-input-dim", type=int, default=MAX_STATIC_INPUTS_DEFAULT,
                   help="maximum independently sampled V inputs in a static model")
    p.add_argument("--max-ode-state-dim", type=int, default=MAX_ODE_STATES_DEFAULT,
                   help="maximum jointly integrated S states in an ODE system")
    p.add_argument("--discipline", default=None,
                   help="discipline label for the prompt (default: inferred or 'science')")
    p.add_argument("--model", default="claude-opus-4-7")
    p.add_argument("--provider", choices=["anthropic", "openrouter"],
                   default="anthropic",
                   help="Model API protocol. OpenRouter uses /chat/completions")
    p.add_argument("--base-url", default=None,
                   help="Provider base URL. Defaults to the selected provider's environment value")
    p.add_argument("--auth-source", choices=["auto", "api_key", "auth_token"],
                   default="auto",
                   help="auto prefers ANTHROPIC_API_KEY then ANTHROPIC_AUTH_TOKEN")
    p.add_argument("--seed", type=int, default=0,
                   help="seed for the per-step coin flips (reproducible)")
    p.add_argument("--output-dir", default=None,
                   help="output dir (default: outputs/Evolved_Equations)")
    p.add_argument("--novelty-check", dest="novelty_check", action="store_true",
                   default=True,
                   help="use the novelty evaluator as a STOP condition: evolve to "
                        "--steps, then keep evolving one step at a time until the "
                        "equation is judged novel (answer 'Yes') or --max-steps is "
                        "reached (default: on)")
    p.add_argument("--no-novelty-check", dest="novelty_check", action="store_false",
                   help="disable novelty checking; evolve exactly --steps steps")
    p.add_argument("--novelty-model", default=None,
                   help="model for the novelty evaluator (default: same as --model)")
    args = p.parse_args()

    if not (0.0 <= args.p_assumption <= 1.0):
        raise SystemExit("--p-assumption must be between 0 and 1")
    if args.steps < 1:
        raise SystemExit("--steps must be at least 1")
    if args.max_static_input_dim < 1:
        raise SystemExit("--max-static-input-dim must be at least 1")
    if args.max_ode_state_dim < 1:
        raise SystemExit("--max-ode-state-dim must be at least 1")

    # Hard cap on steps when novelty gating keeps asking for more.
    max_steps = args.max_steps if args.max_steps is not None else args.steps + 10
    if max_steps < args.steps:
        raise SystemExit(f"--max-steps ({max_steps}) must be >= --steps ({args.steps})")

    rng = random.Random(args.seed)

    # Load the novelty evaluator (same file-path import style as the stage module).
    m_nov = None
    if args.novelty_check:
        m_nov = _load_module("novelty", NOVELTY_CHECK)
    novelty_model = args.novelty_model or args.model

    input_path = Path(args.input)
    usable = _load_usable_equations(input_path)

    # --list: show the catalog and exit (no API key needed, no tokens spent).
    if args.list:
        print(f"\n{len(usable)} usable equation(s) in {input_path}:", file=sys.stderr)
        print(_format_catalog(usable), file=sys.stderr)
        return

    # Resolve which equation to evolve BEFORE touching the API, so the picker
    # (and any mistakes) cost nothing.
    base = _normalize_base_equation(_select_equation(usable, args.id, args.interactive))
    base_id = _eq_id(base)
    scenario_text = base.get("scenario_text", "")
    discipline = args.discipline or base.get("discipline") or "science"

    print(f"\nSelected: {base_id}  ({discipline})", file=sys.stderr)
    _print_equation(base, prefix="  ")

    caller = build_model_caller(
        args.provider,
        base_url=args.base_url,
        auth_source=args.auth_source,
    )

    out_dir = Path(args.output_dir) if args.output_dir else (
        Path(__file__).resolve().parent / "outputs" / "Evolved_Equations"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    lineage_path = out_dir / f"evolution_{base_id}_{timestamp}.jsonl"
    lineage_xlsx = out_dir / f"evolution_{base_id}_{timestamp}.xlsx"

    print("=" * 60, file=sys.stderr)
    print(f"Evolving equation  base_id={base_id}", file=sys.stderr)
    print(f"  discipline={discipline}  min_steps={args.steps}  "
          f"p(assumption)={args.p_assumption}  seed={args.seed}", file=sys.stderr)
    print(f"  assumptions={args.assumption_mode}  static_inputs<={args.max_static_input_dim}  "
          f"ode_states<={args.max_ode_state_dim}", file=sys.stderr)
    print(f"  provider={args.provider}", file=sys.stderr)
    if args.novelty_check:
        print(f"  novelty-gate : on  (check from gen {args.steps}; stop on 'Yes'; "
              f"max_steps={max_steps}; model={novelty_model})", file=sys.stderr)
    else:
        print(f"  novelty-gate : off  (evolve exactly {args.steps} steps)",
              file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    # Generation 0 = the base equation, recorded as-is.
    lineage: list[dict] = []
    gen0 = _record(base, base_id, 0, "base", scenario_text)
    lineage.append(gen0)
    with lineage_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(gen0, ensure_ascii=False) + "\n")

    print("\n[gen 0] base equation:", file=sys.stderr)
    _print_equation(base)

    # Evolve step by step. Without the novelty gate we run exactly --steps steps.
    # With it, --steps is the MINIMUM: we keep evolving one step at a time, and
    # from gen --steps onward we ask the novelty evaluator after each step —
    # stopping as soon as the equation is judged novel ("Yes"), or when we hit
    # --max-steps. The generation-0 base equation is the classical anchor.
    current = base
    stop_reason = "reached step budget"
    step = 0
    while True:
        step += 1
        # Decide the ceiling for this run.
        ceiling = max_steps if args.novelty_check else args.steps
        if step > ceiling:
            step -= 1  # we didn't actually run this step
            if args.novelty_check:
                stop_reason = f"hit max-steps ({max_steps}) without a 'Yes' verdict"
            break

        operation = "change_assumption" if rng.random() < args.p_assumption else "add_term"
        print(f"\n[gen {step}] operation = {operation}", file=sys.stderr, flush=True)
        try:
            evolved = evolve_once(
                caller=caller,
                current=current,
                operation=operation,
                discipline=discipline,
                scenario_text=scenario_text,
                model=args.model,
                strip_fence=_strip_code_fence,
                assumption_mode=args.assumption_mode,
                max_static_inputs=args.max_static_input_dim,
                max_ode_states=args.max_ode_state_dim,
            )
        except Exception as e:
            print(f"    FAILED at gen {step}: {type(e).__name__}: {e}\n"
                  f"    stopping; keeping {len(lineage)-1} successful step(s).",
                  file=sys.stderr, flush=True)
            step -= 1
            stop_reason = f"evolution failed at gen {step + 1}"
            break

        # Novelty gate: only evaluate once we've reached the minimum --steps.
        # The verdict decides whether this is the LAST step.
        novelty = None
        verdict_is_novel = False
        if args.novelty_check and m_nov is not None and step >= args.steps:
            print(f"    [novelty] evaluating (gen {step})...",
                  file=sys.stderr, flush=True)
            try:
                novelty = m_nov.check_novelty(
                    caller=caller,
                    candidate=evolved,
                    discipline=discipline,
                    scenario_text=scenario_text,
                    model=novelty_model,
                    base=base,
                )
                verdict_is_novel = novelty.get("answer") == "Yes"
            except Exception as e:
                print(f"    [novelty] FAILED: {type(e).__name__}: {e}",
                      file=sys.stderr, flush=True)
                novelty = {"answer": "ERROR", "reasoning": f"{type(e).__name__}: {e}"}
                qa_history = getattr(e, "qa_history", None)
                if qa_history:
                    novelty["llm_qa_history"] = qa_history

        rec = _record(evolved, base_id, step, operation, scenario_text, novelty=novelty)
        lineage.append(rec)
        with lineage_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

        print(f"    change: {evolved.get('change_summary','')}", file=sys.stderr)
        _print_equation(evolved)
        if novelty is not None:
            print(f"    novel? {novelty.get('answer')}", file=sys.stderr)
        current = evolved  # feed forward

        # Stop as soon as the equation is judged sufficiently novel.
        if verdict_is_novel:
            stop_reason = f"novelty verdict 'Yes' at gen {step}"
            break

    _build_lineage_xlsx(lineage_xlsx, lineage)

    print("\n" + "=" * 60, file=sys.stderr)
    print(f"Done. {len(lineage)-1} evolution step(s) from base.", file=sys.stderr)
    print(f"  stop reason : {stop_reason}", file=sys.stderr)
    print(f"  lineage : {lineage_path}", file=sys.stderr)
    print(f"  xlsx    : {lineage_xlsx}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)


if __name__ == "__main__":
    main()
