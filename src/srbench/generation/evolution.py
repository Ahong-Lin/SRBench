"""
Equation Evolution: take a base equation and make it progressively richer.
===========================================================================

Feed in ONE equation produced by `auto_workflow.py` (Stage 3 output) and this
script evolves it step by step. By default a scientific-gap diagnosis chooses
ONE of two operations (a random-operation baseline is also available):

  (1) change_assumption — pick a variable/parameter, RELAX or CHANGE the
      physical assumption originally made about it, then RE-DERIVE the equation
      under the new assumption.
  (2) add_term — add one missing generative process.  A shared mechanism
      framework plus a discipline-specific menu keeps Physics, Biology, and AI
      Scaling Laws scientifically grounded without reducing evolution to a
      generic high-order correction.

The output of each step becomes the input to the next, so the formula keeps
growing in complexity. Static relations remain static relations. ODE systems
remain closed ODE systems: their time axis, states, state RHS expressions, and
initial conditions are carried through every generation.

Usage
-----
    export ANTHROPIC_API_KEY="sk-..."

    # Evolve the first equation in a run's equations.jsonl for 5 steps:
    python -m srbench.generation.evolution \
        --input outputs/physics_20260529-2359/equations.jsonl \
        --steps 5

    # Pick a specific equation by its scenario_id:
    python -m srbench.generation.evolution \
        --input outputs/physics_.../equations.jsonl \
        --id m2_classical_mechanics_0_000 \
        --steps 8 --seed 42

    # Legacy random-operation baseline (70% add, 30% assumption-change):
    python -m srbench.generation.evolution --input eq.jsonl --steps 6 \
        --operation-policy random --p-assumption 0.3
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from pydantic import BaseModel, Field

from srbench.common.model_provider import ModelCaller, ModelRequestError, ModelServiceError, build_model_caller
from srbench.common.io import append_jsonl
from srbench.common.expression_syntax import CONDITION_FUNCTIONS, validate_condition_functions
from srbench.generation.ontology import (
    compatible_embedding_patterns,
    fallback_contract,
    load_taxonomy_profile,
    mechanism_menu,
    validate_contract_fields,
)


# novelty_check.py lives next to this file.
NOVELTY_CHECK = Path(__file__).resolve().parent / "novelty.py"
# Evolved equations carry a full mechanism contract and symbol audit. Keep
# enough completion space for that JSON instead of treating truncation as a
# scientific rejection.
# Keep the historical budget by default; recovery runs can lower it when an
# upstream proxy times out on large completion reservations.
EVOLUTION_COMPLETION_TOKENS = int(os.environ.get("SRBENCH_EVOLUTION_MAX_TOKENS", "12000"))
if EVOLUTION_COMPLETION_TOKENS <= 0:
    raise ValueError("SRBENCH_EVOLUTION_MAX_TOKENS must be positive")


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
FreedomChange = Literal[
    "none", "add_input", "add_state", "parameter_to_input", "parameter_to_state",
]

ResponseChangeType = Literal[
    "slope_change", "curvature_change", "interaction_emergence",
    "threshold_surface", "branch_crossover", "phase_shift", "zero_shift",
    "ridge_rotation", "weight_exchange", "asymptotic_change",
]

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


class AddTermAudit(BaseModel):
    """Scientific justification for one ``add_term`` transition.

    This forces an added expression to name a missing *generative process*,
    rather than merely describe a more complicated mathematical form.
    """

    # This is an explanatory free-text category.  It is deliberately not a
    # closed taxonomy: a new scientific domain should not need a source-code
    # update merely to name a valid mechanism.
    mechanism_class: str
    mechanism_claim: str
    parent_reduction: str
    observable_signature: str


class ResponseChange(BaseModel):
    """Structured description of the parent-to-child response change.

    The fields are deliberately descriptive.  They state which observable
    relationship is expected to change; deterministic diagnostics later test
    whether the generated data actually exhibits that change.
    """

    type: ResponseChangeType = "interaction_emergence"
    parent_relation: str
    child_relation: str
    affected_inputs: list[str] = Field(min_length=1)
    observable_effect: str


class DiagnosticGroup(BaseModel):
    """A dimensionless or otherwise interpretable coordinate used for coverage."""

    name: str
    expression: str
    role: str


class EvolutionContract(BaseModel):
    """Machine-readable record of the scientific parent -> child change."""

    operation: Literal["add_term", "change_assumption"]
    parent_shortcut: str = "unspecified"
    response_change: Optional[ResponseChange] = None
    diagnostic_groups: list[DiagnosticGroup] = Field(default_factory=list)
    activation_condition: str = ""
    train_hidden_contrast: str = ""
    continuation_path: str = ""
    freedom_change: FreedomChange = "none"
    promoted_symbol: Optional[str] = None
    promotion_reason: str = ""
    scope_kind: str
    scope_symbols: list[str] = Field(min_length=1)
    structural_role: str
    domain_mechanism_id: str = ""
    domain_mechanism: str
    scientific_mechanism: str
    embedding_pattern: str
    difficulty_rationale: str
    taxonomy_match: Literal["known", "alias", "provisional"] = "provisional"
    assumption_before: str
    assumption_after: str
    before_fragment: str
    after_fragment: str
    parent_reduction: str
    observable_signature: str
    shortcut_blocked: str


class MechanismPlan(BaseModel):
    """First-layer diagnosis made before an equation successor is written."""

    operation: Literal["add_term", "change_assumption"]
    parent_shortcut: str = "unspecified"
    response_change: Optional[ResponseChange] = None
    diagnostic_groups: list[DiagnosticGroup] = Field(default_factory=list)
    activation_condition: str = ""
    train_hidden_contrast: str = ""
    continuation_path: str = ""
    freedom_change: FreedomChange = "none"
    promoted_symbol: Optional[str] = None
    promotion_reason: str = ""
    gap_statement: str
    baseline_assumption: str
    scientific_mechanism: str
    affected_symbols: list[str] = Field(min_length=1)
    rationale: str


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
    add_term_audit: Optional[AddTermAudit] = None
    evolution_contract: Optional[EvolutionContract] = None
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
   Piecewise equality conditions may use Eq(a, b), and combined conditions may
   use And/Or/Not. These predicates belong only in Piecewise branch conditions;
   an entire equation such as Eq(target, rhs) is not a numeric RHS.
2. Keep the same model_family and equation_type as the current model. Declare every
   symbol used, preserve existing symbols unless the scientific re-derivation truly
   removes a mechanism, and give a range suggestion for every NEW symbol and
   every existing parameter promoted to an input or state.
3. symbol_properties distinguishes mathematical roles:
   - O: the target output or target derivative;
   - V: a static independently sampled input, or the ONE ODE time axis only;
   - S: an ODE internal state, which changes along the time trajectory and is never
        independently sampled;
   - P: a fixed parameter for one generated dataset.
"""

_STATIC_RULES = """
STATIC MODEL RULES:
- For static_explicit, expression contains ONLY the numeric RHS f(inputs, parameters).
  Do not include the target, an assignment, or an outer Eq(target, rhs).
- For static_implicit, expression contains ONLY the scalar residual g(...), with
  g(...)=0 understood. Do not wrap the residual in Eq(..., 0).
- V symbols are exactly the independently sampled inputs. S is not allowed.
- Do not introduce time derivatives, initial conditions, or an ode_system.
"""

_ODE_RULES = """
ODE SYSTEM RULES:
- expression is exactly the RHS of the target_state equation.
- All RHS strings contain numeric expressions, not assignments or outer Eq(...).
- ode_system must repeat the same time_symbol and target_state and include every
  state with one local first-order RHS and one finite initial_condition.
- States use S, only the time axis uses V, and parameters use P.
- Every state RHS may reference only the time symbol, declared states, fixed
  parameters, and standard math functions. Do not use x(t), Derivative, Integral,
  delay/history terms, PDE terms, or an ungoverned h(t).
"""

_FREEDOM_RULES = """
DEGREES OF FREEDOM — decide as part of the scientific operation, before choosing
the mathematical embedding. Either operation can need one additional degree of
freedom. Do not add a variable merely to increase dimension.
- none: the existing inputs/states suffice; their roles remain unchanged.
- add_input: introduce ONE new independently sampled V symbol (static only).
- add_state: introduce ONE new S symbol with its own RHS and finite initial
  condition (ODE only). It must influence an existing state; one-way influence
  is sufficient unless the scientific mechanism specifically claims feedback.
- parameter_to_input: an EXISTING P symbol itself becomes V (static only).
- parameter_to_state: an EXISTING P symbol itself becomes S with its own RHS
  and finite initial condition (ODE only).
For the two parameter_to_* choices, promoted_symbol must name that exact parent
P symbol. For all other choices, promoted_symbol must be null. Changing a
coefficient's numerical value is not promotion. Adding a new condition T to
modulate a still-fixed coefficient k is add_input, not parameter_to_input.
promotion_reason explains why existing inputs/states or a fixed parameter are
insufficient; it is required for every non-none choice. Keep old inputs/states
and their roles; release at most ONE new degree of freedom per generation.
Record a physically meaningful parent-recovery condition in the contract.
Use the SAME freedom_change, promoted_symbol, and promotion_reason in the plan
and evolution_contract. Retain the model family; ODE V remains the time axis.
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
  "derivation_notes": "<1-2 sentences on the scientific mechanism>",
  "change_summary": "<1-2 sentences on what changed and why>",
  "assumption_audit": {assumption_audit_schema},
  "add_term_audit": {add_term_audit_schema},
  "evolution_contract": {evolution_contract_schema},
  "ode_system": {ode_system_schema}
}}
The first character of your response must be `{{` and the last must be `}}`.
Do NOT wrap in markdown fences. Do NOT add any prose before or after the JSON.
"""

_EFFECTIVE_EVOLUTION_RULES = """
EFFECTIVE EVOLUTION — evaluate the scored target conditional on the inputs and
observed states actually supplied to the solver. In rationale (planning) and
observable_signature (equation contract), explicitly describe: the parent's
response relationship; the child's changed slope, curvature, peak, threshold,
saturation scale or interaction; and the scientifically admissible conditions
where that change is observable. Distinguish a changed target mapping from a
change only to auxiliary trajectories. Both can be scientifically valid, but
only the former justifies claiming increased target-function complexity.
In shortcut_blocked, explain whether refitting ALL existing parent parameters
could absorb the change across these conditions. If it can, say so honestly;
do not claim a longer expression or another state automatically blocks fitting.
Prefer consequential natural refinements over decorative terms, fixed gain
rescalings, or numerically negligible corrections. Never inflate physical small
quantities just to lower a score, and never hide all evidence in the test region.
For a NEW ODE state, justify its initial condition in derivation_notes: check
whether the chosen value closes a feedback branch or lies on an invariant
zero-effect set. Choose a non-degenerate scientifically allowed initial condition
when appropriate; preserve existing initial conditions. If the scenario requires
an inactive/equilibrium state, document that limitation instead of inventing motion.
Use new_symbol_range_suggestions for admissible activation ranges. Treat these
statements as scientific hypotheses, not proof of measured difficulty.

CANDIDATE SELECTION DISCIPLINE:
Before selecting the one refinement to return, screen possible refinements for:
(a) constant renaming or merging, e.g. k*x -> (k+a)*x with fixed k and a;
(b) algebraic cancellation, an identically zero contribution, or a branch that
cannot activate under the scenario's admissible conditions;
(c) a promoted quantity that remains constant in the intended experiment;
(d) a correction expected to be negligible throughout the admissible domain;
(e) only changing auxiliary trajectories while leaving the scored mapping from
supplied observations unchanged, e.g. making dv/dt complex when scoring dx/dt=v
and v is supplied. Prefer another scientifically justified gap when one of
these applies. Do not select a redundant change just to fill a generation slot.
A parameter's functional refinement IS useful when it creates an observable
response relationship, e.g. temperature-dependent stiffness with varying T;
parameter changes are not forbidden as a category.

CONCRETE DISTINGUISHING CONDITION:
In the existing rationale, name what input/condition varies, what is held fixed,
and one qualitative response contrast that the parent with one shared refitted
parameter set cannot reproduce across those conditions. State the admissible
activation range or scale relationship. For ODEs the contrast must be reachable
under the actual initial-condition contract and observation protocol: do not
claim evidence from unsampled initial conditions or unavailable interventions.
"More nonlinear", "more coupling", or "higher dimensional" alone is insufficient.
Return a concise, checkable scientific justification, not a list of discarded
candidates or private deliberation. If no meaningful contrast is defensible,
state that limitation explicitly; never fabricate scientific effects.

SUCCESSOR IMPLEMENTATION:
Carry that same distinguishing condition into observable_signature. Explain in
shortcut_blocked why a SINGLE parent parameter set cannot reproduce it, rather
than just comparing the parent's old numerical coefficients. For a newly added
input the parent may ignore that input; it must not secretly refit parameters
separately for each input value. Record activation conditions in range suggestions
and any weakness in derivation_notes. Implement the selected mechanism faithfully;
if the contract prevents activation, report it honestly rather than adding an
unrelated term. A completed generation is not evidence of increased difficulty.

RESPONSE-RELATIONSHIP EVOLUTION:
Diagnose one shortcut in the PARENT target mapping: single_gain,
single_threshold, separable_product, additive_separable, latent_occupancy,
single_phase, fixed_environment, or independent_branch. If none fits, name
another concise scenario-specific shortcut; do not force a false category.
Propose one response_change.type from slope_change, curvature_change,
interaction_emergence, threshold_surface, branch_crossover, phase_shift,
zero_shift, ridge_rotation, weight_exchange, asymptotic_change. Describe the
old and new input-to-target relationship and an observable contrast. A monotone
interaction is sufficient; do not invent a zero, resonance, branch, or extra
dimension to satisfy this vocabulary.
List diagnostic_groups as mathematical coordinates already computable from
declared inputs/states and fixed parameters. They are NOT new input columns.
Give an activation_condition, a train_hidden_contrast, and a scientific
continuation_path that recovers the parent law.
"""

_MECHANISM_PLAN_PROMPT = _HEADER + _EFFECTIVE_EVOLUTION_RULES + """
FIRST-LAYER TASK — DIAGNOSE ONE SCIENTIFIC GAP. Do not write a successor
equation yet.

Read the current equation, variable meanings, scenario, baseline assumptions,
and scientific constraints. Identify one realistic next refinement.

Choose ``add_term`` only when the parent completely omits a real generative
process. Choose ``change_assumption`` only when a process already present in
the parent has an overly idealized mathematical form. Do not choose an
operation randomly and do not invent a mechanism merely to make the formula
more difficult. Decide whether implementing this one change needs a new
quantity or requires releasing an existing fixed parameter.

Return a SINGLE JSON object:
{{
  "operation": "add_term | change_assumption",
  "parent_shortcut": "<parent target-mapping shortcut>",
  "response_change": {{"type": "<one response type>", "parent_relation": "<old mapping>",
    "child_relation": "<planned new mapping>", "affected_inputs": ["<existing or planned input/state>"],
    "observable_effect": "<measurable response contrast>"}},
  "diagnostic_groups": [{{"name": "<short id>", "expression": "<numeric SymPy expression>", "role": "<scientific interpretation>"}}],
  "activation_condition": "<physical scale or regime where the response can be seen>",
  "train_hidden_contrast": "<same mechanism visible in training and extended in holdout>",
  "continuation_path": "<scientific parent-recovery limit>",
  "freedom_change": "none | add_input | add_state | parameter_to_input | parameter_to_state",
  "promoted_symbol": null,
  "promotion_reason": "<why this freedom is necessary; empty for none>",
  "gap_statement": "<specific scientific omission or idealization>",
  "baseline_assumption": "<the exact parent assumption to add or relax>",
  "scientific_mechanism": "<specific scenario-natural process>",
  "affected_symbols": ["<one or more declared symbols>"],
  "rationale": "<scientific justification; varied and fixed conditions; concrete parent/child response contrast; admissible activation conditions and limitations>"
}}
The first character must be {{ and the last must be }}. No markdown or prose.
"""

CHANGE_ASSUMPTION_PROMPT = _HEADER + _EFFECTIVE_EVOLUTION_RULES + """
YOUR TASK — CHANGE AN ASSUMPTION:
The first-layer plan below has already identified the scientific gap and
selected this operation. Implement that plan; do not substitute an unrelated
mechanism just because it produces a more complicated formula.

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
    one new independently controllable/measured V input, either as a new symbol
    (add_input) or an existing P symbol (parameter_to_input). State the numeric
    reference_condition and how the successor reduces to the parent there;
  - state_augmentation: ODE ONLY. A formerly quasi-steady or omitted internal
    quantity becomes one new S state (add_state or parameter_to_state). Add its
    RHS and initial condition, explain
    the parent_reduction (e.g. fast relaxation or fixed-state limit), and make the
    full ODE system closed.

Do not use condition_promotion or state_augmentation merely to make the equation
higher-dimensional. The successor must be a natural next refinement for this
specific phenomenon.

In evolution_contract, record the precise parent assumption, changed expression
fragment, recovery limit, observable signature, why a shortcut that ignores
the changed mechanism is structurally inadequate, and the required embedding
pattern. The subfield mechanism menu is advisory, not a whitelist.

"""

ADD_TERM_PROMPT = _HEADER + _EFFECTIVE_EVOLUTION_RULES + """
YOUR TASK — ADD A FUNCTION TERM:
The first-layer plan below has already identified one missing GENERATIVE
PROCESS. ``add_term`` means adding that process to the governing law; it does
NOT mean adding an arbitrary nonlinear mathematical decoration.

Then ADD exactly ONE function term that implements the planned process using
the required embedding pattern. Keep
the existing structure and incorporate the new term; do not simplify away what
is already there. The successor must be richer because the scientific process is
new, not because a coefficient is tiny or an exponent is cosmetically changed.

In add_term_audit, state: the selected mechanism_class; the causal
mechanism_claim; how the added mechanism vanishes or becomes negligible to
recover the parent (parent_reduction); and the qualitative, experimentally
observable pattern that distinguishes child from parent (observable_signature).

DOMAIN MECHANISM MENU:
{domain_mechanisms}

The new process may need one new input/state, or an existing fixed parameter
may need to become an input/state; record that decision in freedom_change.
Keep existing processes and symbols. Preserve the model family/type, time axis,
and existing initial conditions. For a new ODE state also provide its governing
RHS and initial condition so the full system stays closed. Supporting equations
belong to this ONE process; they are not separate evolution operations.
Set assumption_audit to null.

In evolution_contract, name the affected declared symbols, the exact old/new
fragments, the parent-recovery limit, and why the parent cannot reproduce the
new observable signature just by retuning existing coefficients. Record the
required embedding pattern. The subfield mechanism menu is advisory only.

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


def _log_model_attempt(path, *, caller, model, attempt, prompt, raw, started, error=None):
    """Keep model output and the exact validation error, including failed attempts."""
    if path is not None:
        append_jsonl(path, {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "provider": caller.provider if isinstance(caller, ModelCaller) else "offline",
            "model": model, "attempt": attempt,
            "status": "error" if error is not None else "accepted",
            "prompt": prompt, "raw_response": raw,
            "error": f"{type(error).__name__}: {error}" if error is not None else None,
        })


_IDENTIFIER_RE = re.compile(r"\b[A-Za-z_]\w*\b")
_CALLED_NAME_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_SYMPY_CALLS = {
    "Abs", "Max", "Min", "Piecewise", "Heaviside",
    "sin", "cos", "tan", "asin", "acos", "atan",
    "sinh", "cosh", "tanh", "exp", "log", "sqrt",
    "sign", "floor", "ceiling",
} | CONDITION_FUNCTIONS
_SYMPY_NAMES = _SYMPY_CALLS | {"pi", "E", "I", "oo", "nan", "True", "False"}


def _domain_mechanisms(discipline: str, subfield: str | None = None) -> str:
    """Render taxonomy-aware mechanisms, with a conservative legacy fallback."""
    try:
        return mechanism_menu(load_taxonomy_profile(discipline, subfield))
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    normalized = re.sub(r"[^a-z0-9]+", "", (discipline or "").lower())
    if normalized in {"physics", "physicalscience"}:
        return (
            "Physics: use only a scenario-natural mechanism, such as nonlinear "
            "constitutive response, finite capacity, dissipative/drive coupling, "
            "field interaction, a barrier, or a scale crossover."
        )
    if normalized in {"biology", "biologicalscience", "lifescience"}:
        return (
            "Biology: use only a scenario-natural mechanism, such as resource or "
            "carrying-capacity limitation, density dependence, enzyme/substrate "
            "saturation, inhibition, competition, ecological interaction, "
            "environmental stress, or regulated feedback."
        )
    if normalized in {"ai", "aiscalinglaws", "artificialintelligence", "machinelearning", "scalinglaws"}:
        return (
            "AI Scaling Laws: use only a training/data mechanism, such as an "
            "irreducible loss floor, effective-data or data-quality limitation, "
            "model-capacity bottleneck, compute/optimization limitation, "
            "under-training, hyperparameter interaction, or scale crossover."
        )
    return (
        "Use the terminology and causal mechanisms of the named discipline and "
        "scenario. Select a process a domain expert could measure or manipulate."
    )


def _extract_expression_names(
    expression: str,
    declared_symbols: set[str] | None = None,
) -> tuple[set[str], set[str]]:
    """Collect expression names, respecting declared symbols that shadow SymPy constants."""
    try:
        validate_condition_functions(expression)
    except ValueError as exc:
        raise EvolvedEquationValidationError(str(exc)) from exc
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


def _inherited_dimension_track(current: dict, requested: str | None = None) -> str | None:
    """Honor an explicit legacy constraint without inventing a default lock."""
    track = requested or current.get("dimension_track") or current.get("dimension_class")
    if track and track not in {"fixed_univariate", "promotable_multivariate", "multiway"}:
        raise EvolvedEquationValidationError(f"unknown dimension_track '{track}'")
    return track or None


def _allowed_freedom_changes(
    current: dict,
    assumption_mode: AssumptionMode,
    max_static_inputs: int,
    max_ode_states: int,
    dimension_track: str | None = None,
) -> list[str]:
    """Expose existing family/dimension limits to both planning and generation."""
    track = _inherited_dimension_track(current, dimension_track)
    choices = ["none"]
    if assumption_mode == "core":
        return choices
    roles = _symbol_roles(current)
    if _model_family(current) == "static":
        if track == "fixed_univariate" or list(roles.values()).count("V") >= max_static_inputs:
            return choices
        choices.append("add_input")
        if "P" in roles.values():
            choices.append("parameter_to_input")
    elif list(roles.values()).count("S") < max_ode_states:
        choices.append("add_state")
        if "P" in roles.values():
            choices.append("parameter_to_state")
    return choices


def _check_freedom_choice(current: dict, decision: dict, allowed: list[str]) -> None:
    """Check metadata against the parent roles, not scientific plausibility."""
    change = decision.get("freedom_change", "none")
    if change not in allowed:
        raise EvolvedEquationValidationError(
            f"freedom_change '{change}' is incompatible with model family, assumption mode, "
            f"dimension limits or dimension_track ({_inherited_dimension_track(current)}); "
            f"allowed: {', '.join(allowed)}"
        )
    promoted = decision.get("promoted_symbol")
    if change in {"parameter_to_input", "parameter_to_state"}:
        if _symbol_roles(current).get(promoted) != "P":
            raise EvolvedEquationValidationError("promoted_symbol must name an existing P parameter")
    elif promoted is not None:
        raise EvolvedEquationValidationError("promoted_symbol must be null unless an existing P is promoted")
    if change != "none" and not str(decision.get("promotion_reason") or "").strip():
        raise EvolvedEquationValidationError("a freedom change requires promotion_reason")


def _normalize_and_validate_evolved(
    current: dict,
    candidate: dict,
    operation: str,
    assumption_mode: AssumptionMode,
    max_static_inputs: int,
    max_ode_states: int,
    mechanism_profile: dict | None = None,
    dimension_track: str | None = None,
) -> tuple[dict, list[str]]:
    """Validate type, closure, dimensions, and operation-specific invariants."""
    current = _normalize_base_equation(current)
    dimension_track = _inherited_dimension_track(current, dimension_track)
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

    current_roles = _symbol_roles(current)
    current_v_symbols = {symbol for symbol, role in current_roles.items() if role == "V"}
    current_s_symbols = {symbol for symbol, role in current_roles.items() if role == "S"}
    for symbol, role in current_roles.items():
        if role in {"V", "S"} and roles.get(symbol) != role:
            raise EvolvedEquationValidationError("existing V inputs and S states must keep their roles")
    added_active = {symbol for symbol, role in roles.items()
                    if role in {"V", "S"} and current_roles.get(symbol) != role}
    if len(added_active) > 1:
        raise EvolvedEquationValidationError("at most one new degree of freedom is allowed per generation")
    freedom_symbol = next(iter(added_active), None)
    actual_freedom = "none"
    if freedom_symbol is not None:
        prefix = "parameter_to_" if current_roles.get(freedom_symbol) == "P" else "add_"
        actual_freedom = prefix + ("input" if roles[freedom_symbol] == "V" else "state")
    promoted_symbols = {symbol for symbol in added_active if current_roles.get(symbol) == "P"}
    current_ode = None
    if family == "ode":
        current_ode = _validate_ode_structure(current, max_ode_states)
        if (ode_info["time_symbol"], ode_info["target_state"]) != (
            current_ode["time_symbol"], current_ode["target_state"]
        ):
            raise EvolvedEquationValidationError("ODE time_symbol and target_state must remain unchanged")
        if freedom_symbol is not None:
            old_rhs_names: set[str] = set()
            for symbol in current_s_symbols:
                names, _ = _extract_expression_names(ode_info["state_records"][symbol]["rhs"], declared)
                old_rhs_names |= names
            if freedom_symbol not in old_rhs_names:
                raise EvolvedEquationValidationError("a new S state must influence an existing state RHS")

    current_symbols = set(current.get("symbols", []))
    new_symbols = [sym for sym in symbols if sym not in current_symbols and sym != target_symbol]
    range_symbols = set(new_symbols) | promoted_symbols
    range_suggestions = dict(out.get("new_symbol_range_suggestions") or {})
    unexpected = sorted(sym for sym in range_suggestions if sym not in range_symbols)
    if unexpected:
        raise EvolvedEquationValidationError(
            "new_symbol_range_suggestions contains symbols that are neither new nor promoted: " +
            ", ".join(unexpected)
        )
    missing_ranges = sorted(
        sym for sym in range_symbols if not str(range_suggestions.get(sym, "")).strip()
    )
    if missing_ranges:
        raise EvolvedEquationValidationError(
            "missing suggested range for new or promoted symbols: " + ", ".join(missing_ranges)
        )

    if operation not in {"change_assumption", "add_term"}:
        raise EvolvedEquationValidationError(f"unsupported evolution operation '{operation}'")

    contract = out.get("evolution_contract")
    if not isinstance(contract, dict):
        raise EvolvedEquationValidationError(
            "every evolved equation must include an evolution_contract"
        )
    try:
        validate_contract_fields(
            contract,
            mechanism_profile or load_taxonomy_profile("science", None),
            set(symbols) | {target_symbol},
        )
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        raise EvolvedEquationValidationError(str(exc)) from exc
    if contract.get("operation") != operation:
        raise EvolvedEquationValidationError(
            "evolution_contract.operation must match the requested operation"
        )
    contract = dict(contract)
    contract.setdefault("freedom_change", "none")
    contract.setdefault("promoted_symbol", None)
    contract.setdefault("promotion_reason", "")
    allowed = _allowed_freedom_changes(
        current, assumption_mode, max_static_inputs, max_ode_states, dimension_track
    )
    if dimension_track == "fixed_univariate" and v_symbols != current_v_symbols:
        raise EvolvedEquationValidationError("fixed_univariate dimension_track forbids V-input changes")
    _check_freedom_choice(current, contract, allowed)
    if contract["freedom_change"] != actual_freedom:
        raise EvolvedEquationValidationError(
            f"freedom_change must match symbol roles: expected '{actual_freedom}'"
        )
    if promoted_symbols and contract["promoted_symbol"] != freedom_symbol:
        raise EvolvedEquationValidationError("promoted_symbol must match the parameter whose role changed")
    response = contract.get("response_change")
    if response is not None:
        if not isinstance(response, dict):
            raise EvolvedEquationValidationError("evolution_contract.response_change must be an object")
        required_response = ("type", "parent_relation", "child_relation", "affected_inputs", "observable_effect")
        missing_response = [key for key in required_response if not str(response.get(key) or "").strip()
                            and key != "affected_inputs"]
        if missing_response:
            raise EvolvedEquationValidationError(
                "response_change requires " + ", ".join(missing_response)
            )
        if response.get("type") not in {
            "slope_change", "curvature_change", "interaction_emergence", "threshold_surface",
            "branch_crossover", "phase_shift", "zero_shift", "ridge_rotation",
            "weight_exchange", "asymptotic_change",
        }:
            raise EvolvedEquationValidationError("unknown response_change.type")
        affected = response.get("affected_inputs")
        if not isinstance(affected, list) or not affected or any(item not in declared for item in affected):
            raise EvolvedEquationValidationError(
                "response_change.affected_inputs must name declared symbols"
            )
    if contract.get("diagnostic_groups") is not None:
        groups = contract.get("diagnostic_groups") or []
        if not isinstance(groups, list):
            raise EvolvedEquationValidationError("diagnostic_groups must be a list")
        for group in groups:
            if not isinstance(group, dict) or not all(str(group.get(k) or "").strip() for k in ("name", "expression", "role")):
                raise EvolvedEquationValidationError("each diagnostic_group needs name, expression and role")
    if response is not None:
        for key in ("activation_condition", "train_hidden_contrast", "continuation_path"):
            if not str(contract.get(key) or "").strip():
                raise EvolvedEquationValidationError(f"evolution_contract.{key} is required with response_change")
    out["evolution_contract"] = contract
    compact_parent = re.sub(r"\s+", "", str(current.get("expression", "")))
    compact_child = re.sub(r"\s+", "", expression)
    if re.sub(r"\s+", "", str(contract.get("before_fragment", ""))) not in compact_parent:
        raise EvolvedEquationValidationError(
            "evolution_contract.before_fragment must occur in the parent expression; "
            f"received {contract.get('before_fragment')!r}. Copy an unchanged substring "
            "of the parent expression, or copy the complete parent expression."
        )
    if re.sub(r"\s+", "", str(contract.get("after_fragment", ""))) not in compact_child:
        raise EvolvedEquationValidationError(
            "evolution_contract.after_fragment must occur in the child expression; "
            f"received {contract.get('after_fragment')!r}. Copy an unchanged substring "
            "of your expression field, or copy that complete field."
        )

    audit = out.get("assumption_audit")
    if operation == "add_term":
        if audit is not None:
            raise EvolvedEquationValidationError("add_term must set assumption_audit to null")
        add_audit = out.get("add_term_audit")
        if not isinstance(add_audit, dict):
            raise EvolvedEquationValidationError("add_term requires a structured add_term_audit")
        required_audit_text = ("mechanism_claim", "parent_reduction", "observable_signature")
        missing_audit_text = [
            key for key in required_audit_text if not str(add_audit.get(key) or "").strip()
        ]
        if missing_audit_text:
            raise EvolvedEquationValidationError(
                "add_term_audit needs non-empty " + ", ".join(missing_audit_text)
            )
        removed = sorted(set(current.get("symbols", [])) - set(symbols))
        if removed:
            raise EvolvedEquationValidationError(
                "add_term must preserve every existing symbol; removed "
                + ", ".join(removed)
            )
        if family == "ode":
            for symbol in current_s_symbols:
                before = current_ode["state_records"][symbol]["initial_condition"]
                after = ode_info["state_records"][symbol]["initial_condition"]
                if before != after:
                    raise EvolvedEquationValidationError(
                        "add_term cannot change ODE initial conditions"
                    )
    else:
        if out.get("add_term_audit") is not None:
            raise EvolvedEquationValidationError("change_assumption must set add_term_audit to null")
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
            if dimension_track == "fixed_univariate":
                raise EvolvedEquationValidationError(
                    "fixed_univariate dimension_track forbids condition_promotion"
                )
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
    return "CURRENT ODE SYSTEM (preserve existing states; extend only as scientifically planned):\n" + json.dumps(
        ode, ensure_ascii=False, indent=2
    )


def _active_quantity_symbols(eq: dict) -> list[str]:
    """Declared non-output quantities that can carry an embedding pattern."""
    roles = _symbol_roles(eq)
    return [symbol for symbol, role in roles.items() if role in {"V", "S"}]


def sample_embedding_pattern(
    rng: random.Random,
    current: dict,
    operation: str,
    assumption_mode: AssumptionMode = "extended",
    evolution_plan: dict | None = None,
) -> dict:
    """Draw one compatible, weighted embedding pattern reproducibly."""
    current = _normalize_base_equation(current)
    planned_change = (evolution_plan or {}).get("freedom_change", "none")
    active_count = len(_active_quantity_symbols(current)) + (planned_change != "none")
    choices = compatible_embedding_patterns(
        operation=operation,
        model_family=_model_family(current),
        active_quantity_count=active_count,
        assumption_mode=assumption_mode,
    )
    if evolution_plan is not None and planned_change not in {"add_state", "parameter_to_state"}:
        choices = [choice for choice in choices if choice["id"] != "auxiliary_state_feedback"]
    response_type = ((evolution_plan or {}).get("response_change") or {}).get("type")
    preferred = {
        "slope_change": {"state_dependent_coefficient", "multiplicative_modulation"},
        "curvature_change": {"state_dependent_coefficient", "saturating_or_thresholded", "nested_nonlinearity"},
        "interaction_emergence": {"state_coupling", "multiplicative_modulation", "nested_nonlinearity"},
        "threshold_surface": {"state_coupling", "saturating_or_thresholded", "nested_nonlinearity"},
        "branch_crossover": {"competing_processes", "saturating_or_thresholded"},
        "phase_shift": {"multi_timescale", "state_coupling", "nested_nonlinearity"},
        "zero_shift": {"state_coupling", "multi_timescale", "nested_nonlinearity"},
        "ridge_rotation": {"state_coupling", "nested_nonlinearity"},
        "weight_exchange": {"competing_processes", "multiplicative_modulation"},
        "asymptotic_change": {"saturating_or_thresholded", "competing_processes"},
    }.get(response_type, set())
    weights = [max(1, int(choice.get("weight", 1))) * (3 if choice["id"] in preferred else 1)
               for choice in choices]
    return dict(rng.choices(choices, weights=weights, k=1)[0])


def plan_evolution_step(
    caller: ModelCaller,
    current: dict,
    discipline: str,
    scenario_text: str,
    model: str,
    strip_fence,
    *,
    baseline_mechanisms: list[str] | None = None,
    baseline_assumptions: list[str] | None = None,
    scientific_constraints: list[str] | None = None,
    prior_mechanisms: list[str] | None = None,
    assumption_mode: AssumptionMode = "extended",
    max_static_inputs: int = MAX_STATIC_INPUTS_DEFAULT,
    max_ode_states: int = MAX_ODE_STATES_DEFAULT,
    dimension_track: str | None = None,
    max_retries: int = 3,
    trace_path: Path | None = None,
    strict_response_contract: bool = False,
) -> dict:
    """Let the LLM choose an operation by diagnosing the current model gap."""
    current = _normalize_base_equation(current)
    declared = set(current.get("symbols", []))
    allowed = _allowed_freedom_changes(
        current, assumption_mode, max_static_inputs, max_ode_states, dimension_track
    )
    prompt = _MECHANISM_PLAN_PROMPT.format(
        discipline=discipline,
        scenario_text=scenario_text or "(no scenario text recorded)",
        target_symbol=current.get("target_symbol", "y"),
        expression=current.get("expression", ""),
        symbol_table=_symbol_table(current),
        model_family=_model_family(current),
        equation_type=current.get("equation_type"),
        system_block=_system_block(current),
    )
    prompt += (
        "\nRECORDED BASELINE MECHANISMS: "
        + (", ".join(baseline_mechanisms or []) or "(not recorded)")
        + "\nRECORDED BASELINE ASSUMPTIONS: "
        + ("; ".join(baseline_assumptions or []) or "(infer cautiously from the equation and scenario)")
        + "\nSCIENTIFIC CONSTRAINTS: "
        + ("; ".join(scientific_constraints or []) or "(use stated variable meanings and standard domain constraints)")
        + "\nMECHANISMS ALREADY USED IN THIS LINEAGE: "
        + ("; ".join(prior_mechanisms or []) or "(none)")
        + "\nThe affected_symbols must be existing declared V, S, or P symbols; "
          "include the parameter being promoted when applicable. Do not name the output or an undeclared symbol.\n"
        + _FREEDOM_RULES
        + "\nALLOWED freedom_change VALUES FOR THIS PARENT: " + ", ".join(allowed)
        + f"\nDimension limits: {max_static_inputs} static inputs, {max_ode_states} ODE states.\n"
    )
    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        raw = ""
        started = time.monotonic()
        try:
            raw = caller.complete(prompt, model=model, max_tokens=1800, json_mode=True)
            if not raw.strip():
                raise ValueError("empty evolution-plan response")
            plan = MechanismPlan.model_validate(json.loads(strip_fence(raw))).model_dump(exclude_unset=True)
            invalid = [symbol for symbol in plan["affected_symbols"] if symbol not in declared]
            eligible = {symbol for symbol, role in _symbol_roles(current).items() if role in {"V", "S", "P"}}
            inactive = [symbol for symbol in plan["affected_symbols"] if symbol not in eligible]
            if invalid:
                raise ValueError("evolution plan uses undeclared symbols: " + ", ".join(invalid))
            if inactive:
                raise ValueError("evolution plan affected_symbols must be declared V/S/P quantities: " + ", ".join(inactive))
            _check_freedom_choice(current, plan, allowed)
            if plan["promoted_symbol"] is not None and plan["promoted_symbol"] not in plan["affected_symbols"]:
                raise ValueError("affected_symbols must include promoted_symbol")
            if strict_response_contract:
                required = ("parent_shortcut", "response_change", "diagnostic_groups",
                            "activation_condition", "train_hidden_contrast", "continuation_path")
                missing = [key for key in required if key not in plan or plan.get(key) in (None, "", [])]
                if missing:
                    raise ValueError("strict response contract missing " + ", ".join(missing))
            _log_model_attempt(trace_path, caller=caller, model=model, attempt=attempt + 1,
                               prompt=prompt, raw=raw, started=started)
            return plan
        except (ModelRequestError, json.JSONDecodeError, ValueError) as exc:
            _log_model_attempt(trace_path, caller=caller, model=model, attempt=attempt + 1,
                               prompt=prompt, raw=raw, started=started, error=exc)
            if isinstance(exc, ModelServiceError):
                raise
            last_err = exc
            if attempt < max_retries:
                prompt += (
                    "\nPREVIOUS PLAN FAILED: " + f"{type(exc).__name__}: {exc}. "
                    "Return corrected JSON using declared V/S/P symbols and an allowed freedom_change.\n"
                )
                continue
            raise
    raise last_err  # pragma: no cover


def _output_schema_values(
    current: dict,
    operation: str,
) -> tuple[str, str, str, str]:
    """Return JSON snippets required by the operation and inherited model family."""
    if operation == "add_term":
        audit_schema = "null"
        add_term_audit_schema = """{
    "mechanism_class": "<short free-text scientific mechanism category>",
    "mechanism_claim": "<specific causal process missing from the parent>",
    "parent_reduction": "<limit in which the new process vanishes or is negligible>",
    "observable_signature": "<qualitative data pattern distinguishing child from parent>"
  }"""
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
        add_term_audit_schema = "null"
    evolution_contract_schema = """{
    "operation": "__OPERATION__",
    "parent_shortcut": "<copy from plan>",
    "response_change": {"type": "<copy from plan>", "parent_relation": "<old relation>",
      "child_relation": "<new relation>", "affected_inputs": ["<input/state>"],
      "observable_effect": "<response contrast>"},
    "diagnostic_groups": [{"name": "<id>", "expression": "<numeric SymPy expression>", "role": "<scientific role>"}],
    "activation_condition": "<physical activation regime>",
    "train_hidden_contrast": "<training evidence and holdout continuation>",
    "continuation_path": "<parent-recovery limit>",
    "freedom_change": "none | add_input | add_state | parameter_to_input | parameter_to_state",
    "promoted_symbol": null,
    "promotion_reason": "<copy from plan; empty for none>",
    "scope_kind": "unary | pairwise | multiway | state_coupling | time_forcing | memory",
    "scope_symbols": ["<declared symbol>"],
    "structural_role": "contribution | response_law | modulation | interaction | constraint | transition | feedback | heterogeneity | timescale | transport_balance",
    "domain_mechanism_id": "<optional taxonomy id, or empty string>",
    "domain_mechanism": "<specific scientific process>",
    "scientific_mechanism": "<must match the first-layer plan>",
    "embedding_pattern": "<must match the required pattern id>",
    "difficulty_rationale": "<why this embedding is structurally harder than a coefficient-only correction>",
    "taxonomy_match": "known | alias | provisional",
    "assumption_before": "<parent assumption>",
    "assumption_after": "<child mechanism or relaxed assumption>",
    "before_fragment": "<exact parent fragment>",
    "after_fragment": "<exact child fragment>",
    "parent_reduction": "<limit recovering parent>",
    "observable_signature": "<distinguishing pattern>",
    "shortcut_blocked": "<why coefficient retuning or trajectory fitting is insufficient>"
  }""".replace("__OPERATION__", operation)
    if _model_family(current) == "static":
        return audit_schema, add_term_audit_schema, evolution_contract_schema, "null"
    return audit_schema, add_term_audit_schema, evolution_contract_schema, """{
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
    dimension_track: str | None = None,
    mechanism_profile: dict | None = None,
    evolution_plan: dict | None = None,
    embedding_pattern: dict | None = None,
    max_retries: int = 3,
    difficulty_feedback: str | None = None,
    trace_path: Path | None = None,
    strict_response_contract: bool = False,
) -> dict:
    current = _normalize_base_equation(current)
    dimension_track = _inherited_dimension_track(current, dimension_track)
    allowed = _allowed_freedom_changes(
        current, assumption_mode, max_static_inputs, max_ode_states, dimension_track
    )
    mechanism_profile = mechanism_profile or load_taxonomy_profile(
        discipline, current.get("subfield")
    )
    if evolution_plan is not None:
        evolution_plan = MechanismPlan.model_validate(evolution_plan).model_dump(exclude_unset=True)
        if evolution_plan["operation"] != operation:
            raise EvolvedEquationValidationError(
                "evolution_plan.operation must match the requested operation"
            )
        _check_freedom_choice(current, evolution_plan, allowed)
    if embedding_pattern is not None:
        embedding_pattern = dict(embedding_pattern)
        if not embedding_pattern.get("id"):
            raise EvolvedEquationValidationError("embedding_pattern requires an id")
    task_prompt = (
        CHANGE_ASSUMPTION_PROMPT
        if operation == "change_assumption"
        else ADD_TERM_PROMPT
    )
    family = _model_family(current)
    structure_rules = _STATIC_RULES if family == "static" else _ODE_RULES
    audit_schema, add_term_audit_schema, evolution_contract_schema, ode_schema = _output_schema_values(current, operation)
    template = task_prompt + _COMMON_RULES + structure_rules + _FREEDOM_RULES + _OUTPUT_SCHEMA
    assumption_mode_note = (
        "Only use law_refinement, parameter_refinement, boundary_change, or "
        "regime_change. Do not use condition_promotion or state_augmentation."
        if assumption_mode == "core"
        else "condition_promotion and state_augmentation are permitted only when "
        "scientifically justified by this specific system."
    )

    last_err: Exception | None = None
    last_raw = ""
    validation_errors: list[str] = []
    for attempt in range(max_retries + 1):
        raw = ""
        prompt = ""
        started = time.monotonic()
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
                add_term_audit_schema=add_term_audit_schema,
                evolution_contract_schema=evolution_contract_schema,
                ode_system_schema=ode_schema,
                domain_mechanisms=mechanism_menu(mechanism_profile),
            )
            prompt += "\nALLOWED freedom_change VALUES: " + ", ".join(allowed) + "\n"
            prompt += f"Dimension limits: {max_static_inputs} static inputs, {max_ode_states} ODE states.\n"
            prompt += (
                "\nCONTRACT FRAGMENTS ARE EXACT TEXT REFERENCES, not algebraically rewritten formulas.\n"
                "before_fragment must be copied literally from the parent expression below; "
                "after_fragment must be copied literally from your final expression field. "
                "Whitespace may differ. Do not reorder factors, expand, factorize, add grouping, "
                "include an assignment, or quote a different ODE state RHS. "
                "Copying the complete respective expression is valid if the change is global.\n"
                "PARENT EXPRESSION (JSON string): " + json.dumps(current.get("expression", "")) + "\n"
            )
            if dimension_track:
                prompt += (
                    "\nINHERITED DIMENSION CONSTRAINT: " + dimension_track + "\n"
                    "fixed_univariate keeps the V inputs fixed; other legacy tracks allow "
                    "one scientifically justified freedom change under either operation.\n"
                )
            if evolution_plan is not None:
                prompt += (
                    "\nFIRST-LAYER EVOLUTION PLAN (must implement exactly one planned mechanism):\n"
                    + json.dumps(evolution_plan, ensure_ascii=False, indent=2)
                )
            if embedding_pattern is not None:
                prompt += (
                    "\nREQUIRED EMBEDDING PATTERN (chosen randomly but reproducibly by the pipeline):\n"
                    + json.dumps(embedding_pattern, ensure_ascii=False, indent=2)
                    + "\nThe child must use this exact embedding_pattern id. Use at least the number "
                    "of declared active quantities required by the pattern where applicable. Do not quietly "
                    "substitute a different pattern.\n"
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
                    "\nVALIDATION ERRORS IN THIS STEP (correct all of them):\n"
                    + "\n".join(validation_errors)
                    + "\nPREVIOUS RESPONSE TO CORRECT:\n" + last_raw
                    + "\nReturn a corrected JSON that keeps the same scientific mechanism and target symbol, "
                    "declares every symbol used in the expression, uses "
                    "symbol_properties consistently, and provides suggested "
                    "ranges for every newly introduced symbol.\n"
                )
            raw = caller.complete(prompt, model=model, max_tokens=EVOLUTION_COMPLETION_TOKENS, json_mode=True)
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
                mechanism_profile=mechanism_profile,
                dimension_track=dimension_track,
            )
            contract = normalized.get("evolution_contract") or {}
            if strict_response_contract and not contract.get("response_change"):
                raise EvolvedEquationValidationError(
                    "strict response contract requires evolution_contract.response_change"
                )
            if evolution_plan is not None:
                if contract.get("scientific_mechanism", "").strip() != evolution_plan["scientific_mechanism"].strip():
                    raise EvolvedEquationValidationError(
                        "evolution_contract.scientific_mechanism must match the first-layer plan"
                    )
                for field in ("freedom_change", "promoted_symbol", "promotion_reason"):
                    default = "none" if field == "freedom_change" else None if field == "promoted_symbol" else ""
                    if contract.get(field, default) != evolution_plan.get(field, default):
                        raise EvolvedEquationValidationError(
                            f"evolution_contract.{field} must match the first-layer plan"
                        )
                for field in ("parent_shortcut", "activation_condition", "train_hidden_contrast", "continuation_path"):
                    planned = evolution_plan.get(field)
                    if planned and contract.get(field) != planned:
                        raise EvolvedEquationValidationError(
                            f"evolution_contract.{field} must match the first-layer plan"
                        )
                if evolution_plan.get("response_change") is not None and contract.get("response_change") != evolution_plan.get("response_change"):
                    raise EvolvedEquationValidationError(
                        "evolution_contract.response_change must match the first-layer plan"
                    )
                if evolution_plan.get("diagnostic_groups") and contract.get("diagnostic_groups") != evolution_plan.get("diagnostic_groups"):
                    raise EvolvedEquationValidationError(
                        "evolution_contract.diagnostic_groups must match the first-layer plan"
                    )
            if embedding_pattern is not None:
                if contract.get("embedding_pattern") != embedding_pattern["id"]:
                    raise EvolvedEquationValidationError(
                        "evolution_contract.embedding_pattern must match the selected pattern"
                    )
            if dimension_track:
                normalized["dimension_track"] = dimension_track
            normalized["mechanism_profile"] = mechanism_profile
            if evolution_plan is not None:
                normalized["evolution_plan"] = evolution_plan
            if embedding_pattern is not None:
                normalized["selected_embedding_pattern"] = embedding_pattern
            if changes:
                print("      normalized symbol roles: " + "; ".join(changes),
                      file=sys.stderr, flush=True)
            _log_model_attempt(trace_path, caller=caller, model=model, attempt=attempt + 1,
                               prompt=prompt, raw=raw, started=started)
            return normalized
        except (
            ModelRequestError,
            json.JSONDecodeError,
            ValueError,
            EvolvedEquationValidationError,
        ) as e:
            _log_model_attempt(trace_path, caller=caller, model=model, attempt=attempt + 1,
                               prompt=prompt, raw=raw, started=started, error=e)
            if isinstance(e, ModelServiceError):
                raise
            last_err = e
            last_raw = raw
            validation_errors.append(f"{type(e).__name__}: {e}")
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
        "add_term_audit": eq.get("add_term_audit"),
        "evolution_contract": (
            eq.get("evolution_contract")
            if operation != "base"
            else None
        ) or (fallback_contract(eq, operation) if operation != "base" else None),
        "dimension_track": _inherited_dimension_track(eq),
        "mechanism_profile": eq.get("mechanism_profile", {}),
        "evolution_plan": eq.get("evolution_plan") if operation != "base" else None,
        "selected_embedding_pattern": (
            eq.get("selected_embedding_pattern") if operation != "base" else None
        ),
        "ode_system": eq.get("ode_system"),
        "scenario_text": scenario_text,
    }
    contract = rec["evolution_contract"] or {}
    rec.update({
        "freedom_change": contract.get("freedom_change", "none"),
        "promoted_symbol": contract.get("promoted_symbol"),
        "promotion_reason": contract.get("promotion_reason", ""),
        "parent_shortcut": contract.get("parent_shortcut", ""),
        "response_change": contract.get("response_change"),
        "diagnostic_groups": contract.get("diagnostic_groups", []),
        "activation_condition": contract.get("activation_condition", ""),
        "train_hidden_contrast": contract.get("train_hidden_contrast", ""),
        "continuation_path": contract.get("continuation_path", ""),
    })
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
            "add_term_audit": json.dumps(
                rec.get("add_term_audit"), ensure_ascii=False
            ),
            "ode_system": json.dumps(rec.get("ode_system"), ensure_ascii=False),
            "dimension_track": rec.get("dimension_track", ""),
            "freedom_change": rec.get("freedom_change", "none"),
            "promoted_symbol": rec.get("promoted_symbol"),
            "promotion_reason": rec.get("promotion_reason", ""),
            "parent_shortcut": rec.get("parent_shortcut", ""),
            "response_change": json.dumps(rec.get("response_change"), ensure_ascii=False),
            "diagnostic_groups": json.dumps(rec.get("diagnostic_groups", []), ensure_ascii=False),
            "activation_condition": rec.get("activation_condition", ""),
            "train_hidden_contrast": rec.get("train_hidden_contrast", ""),
            "continuation_path": rec.get("continuation_path", ""),
            "evolution_contract": json.dumps(rec.get("evolution_contract"), ensure_ascii=False),
            "mechanism_profile": json.dumps(rec.get("mechanism_profile"), ensure_ascii=False),
            "evolution_plan": json.dumps(rec.get("evolution_plan"), ensure_ascii=False),
            "selected_embedding_pattern": json.dumps(rec.get("selected_embedding_pattern"), ensure_ascii=False),
            "scientific_mechanism": (rec.get("evolution_contract") or {}).get("scientific_mechanism", ""),
            "embedding_pattern": (rec.get("evolution_contract") or {}).get("embedding_pattern", ""),
            "difficulty_rationale": (rec.get("evolution_contract") or {}).get("difficulty_rationale", ""),
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
    p.add_argument("--operation-policy", choices=["guided", "random"], default="guided",
                   help="guided: diagnose a scientific gap before selecting an operation; "
                        "random: retain the legacy coin flip")
    p.add_argument("--embedding-policy", choices=["random"], default="random",
                   help="embedding-pattern selection policy (currently weighted random)")
    p.add_argument("--p-assumption", type=float, default=0.5,
                   help="legacy random-policy probability of change_assumption (ignored by guided)")
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
    p.add_argument("--provider", choices=["anthropic", "openrouter", "openai"],
                   default="anthropic",
                   help="Model API protocol. openai/openrouter use Chat Completions")
    p.add_argument("--base-url", default=None,
                   help="Provider base URL. Defaults to the selected provider's environment value")
    p.add_argument("--auth-source", choices=["auto", "api_key", "auth_token"],
                   default="auto",
                   help="auto prefers ANTHROPIC_API_KEY then ANTHROPIC_AUTH_TOKEN")
    p.add_argument("--seed", type=int, default=0,
                   help="seed for reproducible embedding draws and legacy random operations")
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
        Path.cwd() / "outputs" / "Evolved_Equations"
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    lineage_path = out_dir / f"evolution_{base_id}_{timestamp}.jsonl"
    lineage_xlsx = out_dir / f"evolution_{base_id}_{timestamp}.xlsx"

    print("=" * 60, file=sys.stderr)
    print(f"Evolving equation  base_id={base_id}", file=sys.stderr)
    print(f"  discipline={discipline}  min_steps={args.steps}  "
          f"operation_policy={args.operation_policy}  embedding_policy={args.embedding_policy}  "
          f"seed={args.seed}", file=sys.stderr)
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

        plan = None
        if args.operation_policy == "guided":
            prior_mechanisms = [
                str((item.get("evolution_contract") or {}).get("scientific_mechanism", ""))
                for item in lineage[1:]
            ]
            plan = plan_evolution_step(
                caller=caller, current=current, discipline=discipline,
                scenario_text=scenario_text, model=args.model,
                strip_fence=_strip_code_fence,
                baseline_mechanisms=base.get("baseline_mechanisms", []),
                baseline_assumptions=base.get("baseline_assumptions", []),
                scientific_constraints=base.get("scientific_constraints", []),
                prior_mechanisms=prior_mechanisms,
                assumption_mode=args.assumption_mode,
                max_static_inputs=args.max_static_input_dim,
                max_ode_states=args.max_ode_state_dim,
                trace_path=lineage_path.with_suffix("") / f"gen_{step:03d}_plan.jsonl",
                strict_response_contract=True,
            )
            operation = plan["operation"]
        else:
            operation = "change_assumption" if rng.random() < args.p_assumption else "add_term"
        embedding = sample_embedding_pattern(
            rng, current, operation, args.assumption_mode, evolution_plan=plan
        )
        print(f"\n[gen {step}] operation = {operation}; embedding = {embedding['id']}",
              file=sys.stderr, flush=True)
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
                evolution_plan=plan,
                embedding_pattern=embedding,
                strict_response_contract=True,
                trace_path=lineage_path.with_suffix("") / f"gen_{step:03d}_equation.jsonl",
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
