"""
Standalone Auto Workflow: Subject -> Subfield -> Scenario -> Equation
=====================================================================

This single-file version contains the three API stages needed to generate a
small symbolic-regression benchmark:

  1. Subject    -> subfields (fixed taxonomy, exploratory generation, or extension)
  2. Subfield   -> scenarios (M2 style)
  3. Scenario   -> governing equations

It does not import Problem-Scenario/ or Scenario-equation/. Outputs are saved
incrementally, so partial results remain available if an API call fails.

Providers
---------
``anthropic`` (default) uses the Anthropic Messages API. ``openrouter`` uses
OpenRouter's OpenAI-compatible ``/chat/completions`` endpoint directly.

Example
-------
    export ANTHROPIC_API_KEY="sk-..."
    export ANTHROPIC_BASE_URL="https://code.ppchat.vip/"

    # Formal, reproducible run: read the frozen taxonomy slice.
    python auto_workflow.py --subject biology --scenarios 10 --subfield-source fixed

    # Continue the same run after an interruption; all other options must match.
    python auto_workflow.py --subject biology --scenarios 10 \
        --subfield-source fixed --run-name biology_fixed_seed0 --resume

    # Exploration only: ask the model for a fresh subfield partition.
    python auto_workflow.py --subject biology --scenarios 10 --subfield-source generate

    # Propose additions for human review; this does not generate scenarios.
    python auto_workflow.py --subject biology --scenarios 1 --subfield-source extend \
        --new-subfields 5
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

import anthropic
import httpx
from pydantic import AliasChoices, BaseModel, Field
from mechanism_ontology import load_taxonomy_profile, mechanism_menu

try:
    import pandas as pd
except ImportError:  # xlsx export is optional
    pd = None


TaxonomyContext = Literal["name", "name_description", "name_description_examples"]
Provider = Literal["anthropic", "openrouter"]
SubfieldSource = Literal["fixed", "generate", "extend"]
ModelFamily = Literal["static", "ode"]
EquationType = Literal["static_explicit", "static_implicit", "ode_system"]

MAX_STATIC_INPUTS = 4
MAX_ODE_STATES = 4


# ============================================================
# Schemas
# ============================================================

class Subfield(BaseModel):
    name: str = Field(description="snake_case identifier")
    description: str = Field(description="1-2 sentences naming core concepts")
    example_phenomena: list[str] = Field(
        min_length=3,
        max_length=8,
        description="3-8 concrete phenomena for scenario brainstorming",
    )


class SubfieldsOutput(BaseModel):
    subfields: list[Subfield]


class InputSymbol(BaseModel):
    symbol: str
    description: str
    range: list[float] = Field(min_length=2, max_length=2)


class RequiredDynamicState(BaseModel):
    """A core ODE state required in the baseline dynamical system."""

    symbol: str
    description: str
    initial_range: list[float] = Field(min_length=2, max_length=2)


class Spec(BaseModel):
    # Defaults to static only so pre-model-family checkpoint scenarios remain usable.
    model_family: ModelFamily = "static"
    target_symbol: str
    target_description: str
    input_symbols: list[InputSymbol] = Field(default_factory=list)
    time_symbol: Optional[str] = None
    time_range: Optional[list[float]] = None
    target_state: Optional[str] = None
    # Accept the former field name when resuming older checkpoints, but always
    # write the stricter required_dynamic_states name in new records.
    required_dynamic_states: list[RequiredDynamicState] = Field(
        default_factory=list,
        validation_alias=AliasChoices(
            "required_dynamic_states", "dynamic_state_candidates"
        ),
        serialization_alias="required_dynamic_states",
    )
    expected_behaviors: list[str]
    forbidden_behaviors: list[str]


class Scenario(BaseModel):
    scenario_text: str
    mechanism_tag: str
    functional_family: str
    dimension_track: Literal["fixed_univariate", "promotable_multivariate", "multiway"] = "fixed_univariate"
    baseline_mechanisms: list[str] = Field(default_factory=list)
    baseline_assumptions: list[str] = Field(default_factory=list)
    scientific_constraints: list[str] = Field(default_factory=list)
    refinement_agenda: list[str] = Field(default_factory=list)
    mechanism_profile: dict = Field(default_factory=dict)
    spec: Spec


class ScenarioBatch(BaseModel):
    scenarios: list[Scenario]


class ODEStateEquation(BaseModel):
    symbol: str
    rhs: str
    initial_condition: float
    description: str


class ODESystem(BaseModel):
    time_symbol: str
    target_state: str
    states: list[ODEStateEquation] = Field(min_length=1, max_length=MAX_ODE_STATES)


class EquationOutput(BaseModel):
    equation_type: EquationType
    target_symbol: str
    expression: str
    symbols: list[str]
    symbol_descriptions: list[str]
    symbol_properties: list[str]
    derivation_notes: str
    dimension_class: Literal["fixed_univariate", "promotable_multivariate", "multiway"] = "fixed_univariate"
    mechanism_manifest: dict = Field(default_factory=dict)
    ode_system: Optional[ODESystem] = None


# ============================================================
# Prompts
# ============================================================

SUBFIELD_PROMPT = """\
List the {n} major subfields of {discipline} as taught at the graduate level.

For each subfield, provide:
- "name": snake_case identifier (e.g. "classical_mechanics", "fluid_dynamics")
- "description": 1-2 sentences naming the core concepts and governing equations
- "example_phenomena": 3-8 short phrases naming CONCRETE phenomena studied
  in this subfield. These will seed scenario brainstorming downstream, so
  prefer phenomena that admit closed-form or simple differential-equation
  models from observation data.

Constraints:
- Subfields must be MUTUALLY EXCLUSIVE — minimal conceptual overlap between
  any two. A phenomenon should fit clearly into exactly one subfield.
- Collectively COVER the discipline — together the subfields should span
  the field's standard curriculum.
- Use widely accepted curricular boundaries; do not invent novel categories.
- Do NOT include subfields that belong to other disciplines.

OUTPUT FORMAT — IMPORTANT:
Return a SINGLE JSON object of the exact form:
  {{"subfields": [<subfield_1>, <subfield_2>, ...]}}
Do NOT wrap in markdown code fences. Do NOT add any prose before or after.
The first character of your response must be `{{` and the last must be `}}`.
"""


EXTEND_SUBFIELD_PROMPT = """\
You are extending a frozen graduate-level taxonomy for {discipline}.

The existing taxonomy is listed below. Propose exactly {n} ADDITIONAL major
subfields that are NOT already represented by any listed entry. These are
candidate additions for human review, not automatic replacements.

EXISTING FROZEN SUBFIELDS:
{existing_subfields}

For each proposed candidate, provide:
- "name": a snake_case identifier
- "description": 1-2 sentences naming the core concepts and governing equations
- "example_phenomena": 3-8 short phrases naming concrete phenomena suitable for
  closed-form or simple differential-equation symbolic-regression models

Constraints:
- Do NOT repeat, rename, split, or make a near-synonym of any existing subfield.
- Keep candidate granularity comparable to the existing entries.
- Use widely accepted curricular boundaries and minimize overlap among candidates.
- Do not include subfields belonging primarily to other disciplines.

OUTPUT FORMAT — IMPORTANT:
Return a SINGLE JSON object of the exact form:
  {{"subfields": [<subfield_1>, <subfield_2>, ...]}}
Do NOT wrap in markdown code fences. Do NOT add any prose before or after.
The first character of your response must be `{{` and the last must be `}}`.
"""


M2_PROMPT = """\
You are designing a symbolic regression benchmark.
Discipline: {discipline}
{subfield_context}

Generate {k} diverse scenarios within this subfield.

HARD CONSTRAINTS:
- Stay strictly within the specified subfield.
- The scenario's primary state variables, governing mechanism, and equation
  source must all belong to the specified subfield.
- If a phenomenon spans multiple subfields or disciplines, retain only the
  specified subfield's core mechanism as the dynamic model. Treat all other
  mechanisms as fixed background conditions; they must not become primary
  dynamic terms, target variables, or the main equation source.
- Each scenario must target a different underlying mechanism.
- Try to cover different functional families when possible.
- Do not write equations.
- Do not name specific textbook formulas or canonical law names.
- Choose model_family from the SCIENTIFIC QUESTION, not to add difficulty:
  * "static": independently sampled experimental conditions determine an
    instantaneous response, equilibrium quantity, material property, rate, or
    other algebraic output. No initial condition or time integration is needed.
  * "ode": the phenomenon concerns how internal quantities evolve over time,
    such as accumulation, transport, inertia, feedback, conversion, depletion,
    or relaxation. The states must be jointly evolved from initial conditions.
- For "ode", do not list dynamic states as input_symbols. They are dependent
  quantities on one time trajectory, not independently sampled coordinates.
- Choose a dimension_track: "fixed_univariate" when the phenomenon should remain
  one-input/one-output; "promotable_multivariate" when a realistic omitted
  condition may later become an observed input or ODE state; "multiway" only
  when the mechanism intrinsically requires three or more quantities.
- Also provide baseline_mechanisms (already present in gen0),
  baseline_assumptions (2-4 concrete idealizations made by gen0),
  scientific_constraints (1-4 non-negativity, conservation, boundedness, or
  directionality constraints), and a refinement_agenda (plausible later
  add_term/change_assumption mechanisms). These are prompts and records, not a
  closed whitelist of future mechanisms.

For each scenario output:
- scenario_text: 3-5 sentences of natural language.
- mechanism_tag: short kebab-case tag.
- functional_family: one of
  ["exponential", "power_law", "saturation", "oscillatory",
   "logistic", "polynomial", "piecewise", "mixed"].
- spec.target_symbol
- spec.target_description
- spec.model_family: "static" or "ode".
- For static only: spec.input_symbols, a list of 1-{max_static_inputs}
  independently sampled {{"symbol", "description", "range": [low, high]}}.
  Set time_symbol, time_range, target_state, and required_dynamic_states to null
  or empty lists.
- For ode only: spec.time_symbol (normally "t"), spec.time_range [start, end],
  spec.target_state, and spec.required_dynamic_states, a list of 1-{max_ode_states}
  {{"symbol", "description", "initial_range": [low, high]}} entries. Set
  input_symbols to an empty list. These are the core states that the baseline
  ODE system MUST include exactly once; they are not optional candidates.
  target_symbol should name the target state's derivative, such as "dN_dt" or
  "dv_dt".
- spec.expected_behaviors
- spec.forbidden_behaviors
- dimension_track, baseline_mechanisms, baseline_assumptions,
  scientific_constraints, refinement_agenda

OUTPUT FORMAT:
Return a SINGLE JSON object of the exact form:
  {{"scenarios": [<scenario_1>, <scenario_2>, ...]}}
Do not add prose or markdown fences.
""".replace("{max_static_inputs}", str(MAX_STATIC_INPUTS)).replace(
    "{max_ode_states}", str(MAX_ODE_STATES),
)


STATIC_MODELING_PROMPT = """\
You are an expert in {discipline} performing mathematical modeling.
{subfield_line}
Given the following scenario description, derive the governing equation.

SCENARIO:
{scenario_text}

TARGET VARIABLE: {target_symbol} — {target_description}
INPUT VARIABLES: {input_descriptions}

EVOLUTION CONTEXT:
{evolution_context}

YOUR TASK:
Write one static relation that governs {target_symbol} as a function of the
independently sampled input variables. This must be a concrete symbolic
expression, not a qualitative statement.

REQUIREMENTS:
1. The equation must be written in Python/sympy syntax.
   - Use ** for power, sqrt() for square root, sin(), cos(), exp(), log(),
     Abs(), tanh(), etc.
   - Use descriptive parameter names (omega0, gamma, alpha, F0, etc.)
     for any physical constants/parameters that appear.

2. The equation should be derived from first principles or well-known
   governing laws within {discipline}.
   - For an explicit relation: write target = f(inputs, parameters).
   - For an implicit/transcendental relation: write the FULL implicit expression in
     "expression" field as f(target, inputs, parameters) such that
     f(...) = 0. Do NOT put just "0" — put the entire f(...) expression.
   - Do NOT introduce time derivatives, dynamic states, or initial conditions.

3. Include ALL relevant effects mentioned in the scenario.
   Do NOT simplify away nonlinear terms, coupling terms, or damping
   just to get a cleaner formula.

4. Introduce named parameters for constants. Do NOT use floating-point numbers.

OUTPUT FORMAT — return a SINGLE JSON object:
{{
  "equation_type": "static_explicit" or "static_implicit",
  "target_symbol": "{target_symbol}",
  "expression": "<sympy expression string for the RHS>",
"symbols": ["<target>", "<input1>", "<input2>", ...],
  "symbol_descriptions": ["<desc of target>", "<desc of input1>", ...],
  "symbol_properties": ["O", "V", "V", ...],
  "dimension_class": "{dimension_track}",
  "mechanism_manifest": {{"baseline_mechanisms": ["..."], "active_mechanisms": ["..."]}},
  "derivation_notes": "<1-2 sentences explaining which physical law/model this comes from>",
  "ode_system": null
}}

symbol_properties: "O" for the output/target, "V" for input variables, "P" for parameters.

IMPORTANT:
- The first character of your response must be `{{` and the last must be `}}`.
- Do NOT wrap in markdown fences. Do NOT add prose before or after the JSON.
"""


ODE_MODELING_PROMPT = """\
You are an expert in {discipline} performing dynamical-systems modeling.
{subfield_line}
Given the following scenario description, derive a CLOSED first-order ODE system.

SCENARIO:
{scenario_text}

TIME AXIS: {time_symbol} over {time_range}
TARGET DERIVATIVE: {target_symbol} — {target_description}
TARGET STATE: {target_state}
REQUIRED DYNAMIC STATES: {state_descriptions}

EVOLUTION CONTEXT:
{evolution_context}

YOUR TASK:
Write a concrete first-order ODE system for the internal states. The system must
be closed: every dynamic state has one RHS and an initial condition. The stated
target derivative must be the RHS for target_state. This is a dynamics task, not
a static regression relation.

REQUIREMENTS:
1. Use Python/sympy syntax with bare state symbols inside RHS expressions, e.g.
   "v" and "x", not x(t). Use **, sqrt(), sin(), cos(), exp(), log(), Abs(),
   tanh(), etc. Use descriptive parameter names; do not use floating-point
   literals for physical constants.
2. Use every required state exactly once as an internal state, never as an
   independently sampled input. The state set must exactly match the supplied
   required states: do not omit one and do not invent an additional dynamic state.
3. Each RHS may reference only {time_symbol}, declared states, fixed parameters,
   and standard math functions. Do not leave derivatives, ungoverned functions,
   PDE terms, or delayed/history terms in an RHS.
4. Give every state a finite numeric initial_condition within its suggested
   initial range. Include all relevant mechanisms without adding arbitrary terms.

OUTPUT FORMAT — return a SINGLE JSON object:
{{
  "equation_type": "ode_system",
  "target_symbol": "{target_symbol}",
  "expression": "<RHS for d({target_state})/d{time_symbol}>",
  "symbols": ["{target_symbol}", "{time_symbol}", "<state1>", "<parameter1>", ...],
  "symbol_descriptions": ["<desc of target derivative>", "time", "<state desc>", "<parameter desc>", ...],
  "symbol_properties": ["O", "V", "S", "P", ...],
  "dimension_class": "{dimension_track}",
  "mechanism_manifest": {{"baseline_mechanisms": ["..."], "active_mechanisms": ["..."]}},
  "derivation_notes": "<1-2 sentences explaining the governing mechanism>",
  "ode_system": {{
    "time_symbol": "{time_symbol}",
    "target_state": "{target_state}",
    "states": [
      {{"symbol": "<state1>", "rhs": "<d(state1)/d{time_symbol}>",
       "initial_condition": <finite number>, "description": "<state description>"}}
    ]
  }}
}}

symbol_properties: "O" is the target derivative; "V" is the one independently
sampled time axis; "S" is an internal state that must be jointly integrated;
and "P" is a fixed parameter. States are mathematical variables, but they are
not independently sampled inputs.

IMPORTANT:
- The first character of your response must be `{{` and the last must be `}}`.
- Do NOT wrap in markdown fences. Do NOT add prose before or after the JSON.
"""


# ============================================================
# Generic helpers
# ============================================================

def _strip_code_fence(text: str) -> str:
    s = text.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1:]
        if s.endswith("```"):
            s = s[:-3]
    return s.strip()


def _json_from_response(raw: str) -> dict:
    cleaned = _strip_code_fence(raw)
    parsed = json.loads(cleaned)
    if isinstance(parsed, list):
        return {"scenarios": parsed}
    return parsed


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _append_jsonl(path: Path, item: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")


def _load_jsonl(path: Path) -> list[dict]:
    """Load a checkpoint JSONL and report the exact corrupt line, if any."""
    if not path.exists():
        return []
    records: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(
                    f"Cannot resume: invalid JSON in {path} at line {line_no}: {exc}"
                ) from exc
            if not isinstance(item, dict):
                raise SystemExit(
                    f"Cannot resume: {path} line {line_no} is not a JSON object."
                )
            records.append(item)
    return records


def _write_jsonl(path: Path, items: list[dict]) -> None:
    """Rewrite a normalized checkpoint file after loading legacy failed rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def _load_json_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Cannot resume: invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"Cannot resume: {path} is not a JSON object.")
    return value


def _assert_resume_config(existing: dict, expected: dict, meta_path: Path) -> None:
    """Prevent a resumed run from silently changing its experimental treatment."""
    mismatches = []
    for key, value in expected.items():
        if key not in existing:
            mismatches.append(f"{key}: missing from saved metadata")
        elif existing[key] != value:
            mismatches.append(f"{key}: saved={existing[key]!r}, requested={value!r}")
    if mismatches:
        raise SystemExit(
            f"Cannot resume {meta_path}: configuration changed:\n  "
            + "\n  ".join(mismatches)
        )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fixed_equation_scenario(equation: dict, discipline: str) -> dict:
    """Adapt a reviewed Stage-3 seed into the common scenario checkpoint shape."""
    symbols = equation.get("symbols", [])
    descriptions = equation.get("symbol_descriptions", [])
    properties = equation.get("symbol_properties", [])
    inputs = []
    for symbol, description, role in zip(symbols, descriptions, properties):
        if role == "V":
            inputs.append({"symbol": symbol, "description": description})
    scenario_id = equation.get("scenario_id") or equation.get("id")
    if not isinstance(scenario_id, str) or not scenario_id:
        raise SystemExit("Fixed equation records require a non-empty scenario_id.")
    expression = equation.get("expression")
    if not isinstance(expression, str) or not expression.strip():
        raise SystemExit(f"Fixed equation '{scenario_id}' has no expression.")
    return {
        "id": scenario_id,
        "discipline": discipline,
        "subfield": equation.get("subfield", ""),
        "mechanism_tag": "fixed_literature_seed",
        "functional_family": "fixed_equation",
        "scenario_text": equation.get("scenario_text", ""),
        "generation_mode": "fixed",
        "spec": {
            "model_family": equation.get("model_family", "static"),
            "target_symbol": equation.get("target_symbol", "y"),
            "target_description": descriptions[0] if descriptions else "target quantity",
            "input_symbols": inputs,
            "expected_behaviors": [],
            "forbidden_behaviors": [],
        },
    }


def _run_fixed_equation_import(
    args: argparse.Namespace,
    taxonomy_path: Path,
    source_path: Path,
    expected_count: int | None = None,
) -> None:
    """Write fixed gen0 equations using the same checkpoints as Stage 3."""
    records = _load_jsonl(source_path)
    if not records:
        raise SystemExit(f"Fixed equation source is empty: {source_path}")
    if expected_count is not None and len(records) != expected_count:
        raise SystemExit(
            f"Fixed equation source has {len(records)} records, but taxonomy requires "
            f"{expected_count}: {source_path}"
        )
    equation_ids: set[str] = set()
    equations: list[dict] = []
    scenarios: list[dict] = []
    for raw in records:
        item = dict(raw)
        scenario = _fixed_equation_scenario(item, args.subject)
        scenario_id = scenario["id"]
        if scenario_id in equation_ids:
            raise SystemExit(f"Duplicate fixed equation id: {scenario_id}")
        equation_ids.add(scenario_id)
        item["scenario_id"] = scenario_id
        item["discipline"] = args.subject
        item["subfield"] = scenario["subfield"]
        item["generation_mode"] = "fixed"
        scenarios.append(scenario)
        equations.append(item)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_out = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent / "outputs"
    run_name = args.run_name or f"{args.subject}_fixed_{timestamp}"
    scenarios_dir = base_out / "Scenarios" / run_name
    equations_dir = base_out / "Equations" / run_name
    checkpoint_paths = [
        scenarios_dir / "subfields.json", scenarios_dir / "scenarios.jsonl",
        equations_dir / "equations.jsonl", equations_dir / "run_meta.json",
    ]
    existing = [path for path in checkpoint_paths if path.exists()]
    if existing:
        raise SystemExit(
            f"Run '{run_name}' already has checkpoint files; choose a new --run-name: "
            + ", ".join(str(path) for path in existing)
        )
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    equations_dir.mkdir(parents=True, exist_ok=True)
    taxonomy, subfields = _load_taxonomy_subject(taxonomy_path, args.subject)
    _write_json(scenarios_dir / "subfields.json", {
        "discipline": args.subject, "subfield_source": "fixed",
        "taxonomy_file": str(taxonomy_path),
        "taxonomy_sha256": _sha256_file(taxonomy_path), "subfields": subfields,
    })
    _write_jsonl(scenarios_dir / "scenarios.jsonl", scenarios)
    _write_jsonl(equations_dir / "equations.jsonl", equations)
    _write_jsonl(equations_dir / "equation_failures.jsonl", [])
    _build_combined_xlsx(equations_dir / "pipeline.xlsx", scenarios, equations)
    _write_json(equations_dir / "run_meta.json", {
        "status": "complete", "run_name": run_name, "subject": args.subject,
        "subfield_source": "fixed", "equation_mode": "fixed",
        "fixed_equation_source": str(source_path),
        "fixed_equation_sha256": _sha256_file(source_path),
        "n_subfields": len(subfields), "subfield_names": [sf["name"] for sf in subfields],
        "n_scenarios_generated": len(scenarios), "n_equations_ok": len(equations),
        "n_equations_failed": 0, "timestamp": timestamp,
    })
    _write_json(equations_dir / "progress.json", {
        "stage": "complete", "n_scenarios_generated": len(scenarios),
        "n_equations_ok": len(equations), "n_equations_failed": 0,
        "status": "complete",
    })
    print(f"Fixed equations imported: {len(equations)}", file=sys.stderr)
    print(f"  Scenarios: {scenarios_dir}", file=sys.stderr)
    print(f"  Equations: {equations_dir}", file=sys.stderr)


def _next_scenario_index(records: list[dict], subfield: str, seed: int) -> int:
    prefix = f"m2_{subfield}_{seed}_"
    indices = []
    for record in records:
        scenario_id = str(record.get("id", ""))
        if scenario_id.startswith(prefix):
            suffix = scenario_id[len(prefix):]
            if suffix.isdigit():
                indices.append(int(suffix))
    return max(indices, default=-1) + 1


def _flatten_input_descriptions(input_symbols: list[dict]) -> str:
    parts = []
    for s in input_symbols:
        sym = s.get("symbol", "?")
        desc = s.get("description", "")
        rng = s.get("range")
        if isinstance(rng, (list, tuple)) and len(rng) == 2:
            parts.append(f"{sym}: {desc} (range {rng[0]} to {rng[1]})")
        else:
            parts.append(f"{sym}: {desc}")
    return "; ".join(parts)


def _flatten_state_descriptions(states: list[dict]) -> str:
    parts = []
    for state in states:
        symbol = state.get("symbol", "?")
        description = state.get("description", "")
        initial_range = state.get("initial_range")
        if isinstance(initial_range, (list, tuple)) and len(initial_range) == 2:
            parts.append(
                f"{symbol}: {description} (initial range {initial_range[0]} to "
                f"{initial_range[1]})"
            )
        else:
            parts.append(f"{symbol}: {description}")
    return "; ".join(parts)


_IDENTIFIER_RE = re.compile(r"\b[A-Za-z_]\w*\b")
_CALLED_NAME_RE = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
_MATH_CALLS = {
    "Abs", "Max", "Min", "Piecewise", "Heaviside",
    "sin", "cos", "tan", "asin", "acos", "atan",
    "sinh", "cosh", "tanh", "exp", "log", "sqrt",
    "sign", "floor", "ceiling",
}
_MATH_NAMES = _MATH_CALLS | {"pi", "E", "I", "oo", "nan", "True", "False"}


def _expression_names(expression: str, declared: set[str]) -> tuple[set[str], set[str]]:
    """Return symbols and non-math function calls referenced by an expression."""
    names = set(_IDENTIFIER_RE.findall(expression))
    called = set(_CALLED_NAME_RE.findall(expression))
    custom_calls = {name for name in called if name not in _MATH_CALLS}
    return ({name for name in names if name not in _MATH_NAMES} | (names & declared),
            custom_calls)


def _validate_scenario_spec(spec: Spec) -> None:
    """Reject model-family metadata that would make Stage 3 ambiguous."""
    if spec.model_family == "static":
        if not 1 <= len(spec.input_symbols) <= MAX_STATIC_INPUTS:
            raise ValueError(
                f"static scenarios need 1-{MAX_STATIC_INPUTS} input_symbols"
            )
        if (spec.time_symbol is not None or spec.time_range is not None
                or spec.target_state is not None or spec.required_dynamic_states):
            raise ValueError("static scenarios cannot declare ODE time/state metadata")
        return

    if spec.input_symbols:
        raise ValueError("ODE scenarios must keep input_symbols empty; states are not inputs")
    if not spec.time_symbol or not spec.target_state:
        raise ValueError("ODE scenarios need time_symbol and target_state")
    if not isinstance(spec.time_range, list) or len(spec.time_range) != 2:
        raise ValueError("ODE scenarios need a two-value time_range")
    if not 1 <= len(spec.required_dynamic_states) <= MAX_ODE_STATES:
        raise ValueError(
            f"ODE scenarios need 1-{MAX_ODE_STATES} required_dynamic_states"
        )
    state_names = [state.symbol for state in spec.required_dynamic_states]
    if len(state_names) != len(set(state_names)):
        raise ValueError("ODE required_dynamic_states must have distinct symbols")
    if spec.target_state not in state_names:
        raise ValueError("ODE target_state must be one required_dynamic_state")


def _validate_equation_output(output: EquationOutput, spec: Spec) -> None:
    """Verify the model family and ODE closure before saving a generated equation."""
    if output.target_symbol != spec.target_symbol:
        raise ValueError(
            f"equation target_symbol '{output.target_symbol}' does not match scenario "
            f"target '{spec.target_symbol}'"
        )
    if len(output.symbols) != len(output.symbol_descriptions) or (
            len(output.symbols) != len(output.symbol_properties)):
        raise ValueError("symbols, descriptions, and properties must have equal lengths")
    if len(output.symbols) != len(set(output.symbols)):
        raise ValueError("equation symbols must be unique")
    if [symbol for symbol, role in zip(output.symbols, output.symbol_properties)
            if role == "O"] != [output.target_symbol]:
        raise ValueError("exactly one O role is required and it must be target_symbol")

    declared = set(output.symbols)
    expression_names, _ = _expression_names(output.expression, declared)
    unknown = sorted(expression_names - declared)
    if unknown:
        raise ValueError("expression uses undeclared symbols: " + ", ".join(unknown))

    if spec.model_family == "static":
        if output.equation_type not in {"static_explicit", "static_implicit"}:
            raise ValueError("static scenarios must return a static equation_type")
        if output.ode_system is not None:
            raise ValueError("static equations cannot include ode_system")
        invalid_roles = sorted(set(output.symbol_properties) - {"O", "V", "P"})
        if invalid_roles:
            raise ValueError(
                "static equations may use only O, V, and P roles; got "
                + ", ".join(invalid_roles)
            )
        expected_inputs = {item.symbol for item in spec.input_symbols}
        observed_inputs = {symbol for symbol, role in zip(
            output.symbols, output.symbol_properties
        ) if role == "V"}
        if observed_inputs != expected_inputs:
            raise ValueError(
                "static V symbols must exactly match scenario input_symbols; got "
                f"{sorted(observed_inputs)}, expected {sorted(expected_inputs)}"
            )
        return

    if output.equation_type != "ode_system" or output.ode_system is None:
        raise ValueError("ODE scenarios must return equation_type='ode_system' with ode_system")
    ode = output.ode_system
    if ode.time_symbol != spec.time_symbol or ode.target_state != spec.target_state:
        raise ValueError("ode_system time_symbol/target_state must match the scenario")
    if not 1 <= len(ode.states) <= MAX_ODE_STATES:
        raise ValueError(f"ode_system must contain 1-{MAX_ODE_STATES} states")

    state_names = [state.symbol for state in ode.states]
    if len(state_names) != len(set(state_names)):
        raise ValueError("ode_system states must have distinct symbols")
    if ode.target_state not in state_names:
        raise ValueError("ode_system target_state must be listed in states")
    invalid_roles = sorted(set(output.symbol_properties) - {"O", "V", "S", "P"})
    if invalid_roles:
        raise ValueError(
            "ODE equations may use only O, V, S, and P roles; got "
            + ", ".join(invalid_roles)
        )
    required_names = {state.symbol for state in spec.required_dynamic_states}
    if set(state_names) != required_names:
        raise ValueError(
            "ode_system states must exactly match scenario required_dynamic_states; got "
            f"{sorted(state_names)}, expected {sorted(required_names)}"
        )
    candidate_ranges = {
        state.symbol: state.initial_range for state in spec.required_dynamic_states
    }

    allowed = set(state_names) | {ode.time_symbol}
    parameters = {
        symbol for symbol, role in zip(output.symbols, output.symbol_properties)
        if role == "P"
    }
    if output.target_symbol not in declared or ode.time_symbol not in declared:
        raise ValueError("ODE symbols must declare target_symbol and time_symbol")
    if output.symbol_properties[output.symbols.index(ode.time_symbol)] != "V":
        raise ValueError("ODE time_symbol must have V role")
    if any(symbol not in declared for symbol in state_names):
        raise ValueError("ODE states must be declared in symbols")
    non_state_roles = [
        symbol for symbol in state_names
        if output.symbol_properties[output.symbols.index(symbol)] != "S"
    ]
    if non_state_roles:
        raise ValueError(
            "ODE states must have S role: " + ", ".join(sorted(non_state_roles))
        )
    ode_v_symbols = {
        symbol for symbol, role in zip(output.symbols, output.symbol_properties)
        if role == "V"
    }
    if ode_v_symbols != {ode.time_symbol}:
        raise ValueError(
            "ODE V symbols must contain only the time axis; got "
            f"{sorted(ode_v_symbols)}"
        )

    target_rhs = None
    for state in ode.states:
        if not math.isfinite(state.initial_condition):
            raise ValueError(f"state '{state.symbol}' needs a finite initial_condition")
        lo, hi = candidate_ranges[state.symbol]
        if not min(lo, hi) <= state.initial_condition <= max(lo, hi):
            raise ValueError(
                f"state '{state.symbol}' initial_condition is outside its scenario range"
            )
        names, calls = _expression_names(state.rhs, declared)
        unknown = sorted(names - allowed - parameters)
        if unknown:
            raise ValueError(
                f"state '{state.symbol}' RHS uses undeclared/non-state symbols: "
                + ", ".join(unknown)
            )
        if calls:
            raise ValueError(
                f"state '{state.symbol}' RHS contains ungoverned function calls: "
                + ", ".join(sorted(calls))
            )
        if "Derivative" in state.rhs or "Integral" in state.rhs:
            raise ValueError(f"state '{state.symbol}' RHS must be first-order and local")
        if state.symbol == ode.target_state:
            target_rhs = state.rhs

    if target_rhs != output.expression:
        raise ValueError("expression must exactly equal the target state's RHS")


def _allocate_counts(total: int, n_parts: int) -> list[int]:
    if n_parts <= 0:
        return []
    base = total // n_parts
    rem = total % n_parts
    return [base + (1 if i < rem else 0) for i in range(n_parts)]


def _chunk_counts(total: int, batch_size: int) -> list[int]:
    if total <= 0:
        return []
    if batch_size <= 0:
        return [total]
    chunks = []
    remaining = total
    while remaining > 0:
        count = min(batch_size, remaining)
        chunks.append(count)
        remaining -= count
    return chunks


def roll_subfield_count(scenarios: int, rng: random.Random) -> int:
    if scenarios <= 1:
        return 1
    center = math.sqrt(scenarios)
    low = max(1, math.floor(center * 0.8))
    high = max(low + 1, math.ceil(center * 1.25))
    high = min(high, scenarios)
    low = min(low, high)
    return rng.randint(low, high)


def _format_subfield_context(
    subfield: dict,
    taxonomy_context: TaxonomyContext,
) -> str:
    lines = [f"Subfield: {subfield['name']}"]
    if taxonomy_context in ("name_description", "name_description_examples"):
        desc = subfield.get("description")
        if desc:
            lines.append(f"Subfield description: {desc}")
    if taxonomy_context == "name_description_examples":
        phenomena = subfield.get("example_phenomena") or []
        if phenomena:
            lines.append("")
            lines.append("Reference phenomena in this subfield:")
            lines.extend(f"  - {p}" for p in phenomena)
    return "\n".join(lines)


def _load_taxonomy_subject(taxonomy_path: Path, subject: str) -> tuple[dict, list[dict]]:
    """Load one ordered subject slice from a reviewed taxonomy file."""
    if not taxonomy_path.exists():
        raise SystemExit(f"Taxonomy file not found: {taxonomy_path}")
    try:
        taxonomy = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid taxonomy JSON in {taxonomy_path}: {exc}") from exc

    subjects = taxonomy.get("subjects")
    if not isinstance(subjects, dict):
        raise SystemExit(f"Taxonomy file has no object at 'subjects': {taxonomy_path}")
    entry = subjects.get(subject)
    if not isinstance(entry, dict):
        available = ", ".join(sorted(subjects)) or "(none)"
        raise SystemExit(
            f"Subject '{subject}' is not in {taxonomy_path}. Available: {available}"
        )
    subfields = entry.get("subfields")
    if not isinstance(subfields, list) or not subfields:
        raise SystemExit(f"Subject '{subject}' has no non-empty 'subfields' list.")

    cleaned: list[dict] = []
    names: set[str] = set()
    for i, subfield in enumerate(subfields, 1):
        if not isinstance(subfield, dict) or not isinstance(subfield.get("name"), str):
            raise SystemExit(
                f"Invalid subfield #{i} in '{subject}': every entry needs a string name."
            )
        name = subfield["name"].strip()
        if not name or name in names:
            raise SystemExit(f"Duplicate/empty subfield name '{name}' in '{subject}'.")
        names.add(name)
        cleaned.append(dict(subfield, name=name))
    return taxonomy, cleaned


def _resolve_fixed_subfields(
    taxonomy_path: Path,
    subject: str,
    requested_n: int | None,
) -> tuple[list[dict], int]:
    """Select the stable leading slice used by a formal benchmark run."""
    taxonomy, available = _load_taxonomy_subject(taxonomy_path, subject)
    entry = taxonomy["subjects"][subject]
    default_n = entry.get("default_n")
    if requested_n is None:
        if not isinstance(default_n, int) or default_n < 1:
            raise SystemExit(
                f"Subject '{subject}' needs a positive default_n, or pass --n-subfields."
            )
        requested_n = default_n
    if requested_n < 1:
        raise SystemExit("--n-subfields must be positive.")
    if requested_n > len(available):
        raise SystemExit(
            f"Requested {requested_n} subfields, but '{subject}' has only "
            f"{len(available)} in {taxonomy_path}."
        )
    return available[:requested_n], requested_n


def _existing_subfield_block(subfields: list[dict]) -> str:
    """Compact context for asking the model for non-overlapping extensions."""
    rows = []
    for i, subfield in enumerate(subfields, 1):
        desc = str(subfield.get("description", "")).strip()
        rows.append(f"{i}. {subfield['name']}: {desc or '(no description)'}")
    return "\n".join(rows)


def _build_client_kwargs(
    api_key: str | None,
    auth_token: str | None,
    base_url: str | None,
    auth_source: str,
) -> tuple[dict, str]:
    kwargs = {}
    if base_url:
        kwargs["base_url"] = base_url.strip()

    if auth_source == "api_key":
        if not api_key:
            raise SystemExit("Missing ANTHROPIC_API_KEY.")
        kwargs["api_key"] = api_key.strip()
        return kwargs, "api_key"

    if auth_source == "auth_token":
        if not auth_token:
            raise SystemExit("Missing ANTHROPIC_AUTH_TOKEN.")
        kwargs["auth_token"] = auth_token.strip()
        return kwargs, "auth_token"

    if api_key:
        kwargs["api_key"] = api_key.strip()
        return kwargs, "api_key"
    if auth_token:
        kwargs["auth_token"] = auth_token.strip()
        return kwargs, "auth_token"

    raise SystemExit(
        "Missing authentication. Set ANTHROPIC_API_KEY or ANTHROPIC_AUTH_TOKEN."
    )


class OpenRouterRequestError(RuntimeError):
    """HTTP error returned by OpenRouter, with a compact safe error message."""


class ModelCaller:
    """Minimal adapter over the two API protocols used by this workflow."""

    def __init__(
        self,
        provider: Provider,
        *,
        anthropic_client: anthropic.Anthropic | None = None,
        openrouter_api_key: str | None = None,
        openrouter_base_url: str | None = None,
    ) -> None:
        self.provider = provider
        self.anthropic_client = anthropic_client
        self.openrouter_api_key = openrouter_api_key
        self.openrouter_base_url = openrouter_base_url

    def complete(self, prompt: str, model: str, max_tokens: int) -> str:
        if self.provider == "anthropic":
            if self.anthropic_client is None:  # pragma: no cover - guarded at setup
                raise RuntimeError("Anthropic client was not initialized.")
            message = self.anthropic_client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return _read_text_from_message(message)

        if not self.openrouter_api_key or not self.openrouter_base_url:
            raise RuntimeError("OpenRouter client was not initialized.")
        endpoint = self.openrouter_base_url.rstrip("/") + "/chat/completions"
        response = httpx.post(
            endpoint,
            headers={
                "Authorization": f"Bearer {self.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/llm-srbench",
                "X-Title": "LLM-SRBench v5",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
            },
            timeout=120.0,
        )
        if response.is_error:
            try:
                detail = response.json().get("error", response.text)
            except json.JSONDecodeError:
                detail = response.text
            raise OpenRouterRequestError(
                f"OpenRouter HTTP {response.status_code}: {str(detail)[:1000]}"
            )
        try:
            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise OpenRouterRequestError(
                f"OpenRouter returned an unexpected response: {response.text[:1000]}"
            ) from exc
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "".join(
                item.get("text", "") for item in content if isinstance(item, dict)
            )
        raise OpenRouterRequestError("OpenRouter response content was not text.")


def _retryable_errors() -> tuple[type[BaseException], ...]:
    return (
        anthropic.APITimeoutError,
        anthropic.APIConnectionError,
        httpx.RemoteProtocolError,
        httpx.TimeoutException,
        httpx.NetworkError,
        OpenRouterRequestError,
        json.JSONDecodeError,
        ValueError,
    )


def _read_text_from_message(message) -> str:
    return "".join(b.text for b in message.content if b.type == "text")


def _failure_hint(
    err: Exception,
    model: str,
    base_url: str | None,
    auth_source: str,
    provider: Provider,
) -> str | None:
    if provider == "openrouter" and isinstance(err, OpenRouterRequestError):
        return (
            "OpenRouter request failed.\n"
            f"  model       : {model}\n"
            f"  base_url    : {base_url}\n"
            "Common fixes:\n"
            "  - verify OPENROUTER_API_KEY is active and has available credit;\n"
            "  - use a model slug listed at https://openrouter.ai/models;\n"
            "  - inspect the OpenRouter HTTP status and message above."
        )
    if err.__class__.__name__ != "PermissionDeniedError":
        return None
    return (
        "PermissionDeniedError: the remote API/proxy blocked the request.\n"
        f"  model       : {model}\n"
        f"  base_url    : {base_url or '<official default>'}\n"
        f"  auth_source : {auth_source}\n"
        "Common fixes:\n"
        "  - verify ANTHROPIC_BASE_URL matches the key/token you sourced;\n"
        "  - if your .env provides ANTHROPIC_AUTH_TOKEN, retry with --auth-source auth_token;\n"
        "  - try a model allowed by your proxy with --model <model-name>;\n"
        "  - reduce --batch-size if the proxy blocks large requests."
    )


# ============================================================
# Stage 1: subject -> subfields
# ============================================================

def expand_discipline(
    caller: ModelCaller,
    discipline: str,
    n: int,
    model: str,
    max_retries: int = 3,
) -> list[dict]:
    prompt = SUBFIELD_PROMPT.format(discipline=discipline, n=n)
    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            raw = caller.complete(prompt, model, max_tokens=8000)
            if not raw.strip():
                raise ValueError("empty response")
            payload = json.loads(_strip_code_fence(raw))
            validated = SubfieldsOutput.model_validate(payload)
            return [s.model_dump() for s in validated.subfields]
        except _retryable_errors() as e:
            last_err = e
            if attempt < max_retries:
                print(f"    retry {attempt + 1}: {type(e).__name__}: {e}",
                      file=sys.stderr, flush=True)
                continue
            raise
    raise last_err  # pragma: no cover


def propose_subfield_extensions(
    caller: ModelCaller,
    discipline: str,
    existing_subfields: list[dict],
    n: int,
    model: str,
    max_retries: int = 3,
) -> list[dict]:
    """Ask for review candidates without ever editing the frozen taxonomy."""
    prompt = EXTEND_SUBFIELD_PROMPT.format(
        discipline=discipline,
        n=n,
        existing_subfields=_existing_subfield_block(existing_subfields),
    )
    existing_names = {subfield["name"] for subfield in existing_subfields}
    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            raw = caller.complete(prompt, model, max_tokens=8000)
            if not raw.strip():
                raise ValueError("empty response")
            payload = json.loads(_strip_code_fence(raw))
            candidates = [s.model_dump() for s in SubfieldsOutput.model_validate(payload).subfields]
            names = [candidate["name"] for candidate in candidates]
            duplicates = sorted({name for name in names if names.count(name) > 1})
            overlaps = sorted(set(names) & existing_names)
            if len(candidates) != n:
                raise ValueError(f"expected {n} extension candidates, got {len(candidates)}")
            if duplicates:
                raise ValueError("duplicate extension candidate names: " + ", ".join(duplicates))
            if overlaps:
                raise ValueError("extensions duplicate existing names: " + ", ".join(overlaps))
            return candidates
        except _retryable_errors() as e:
            last_err = e
            if attempt < max_retries:
                print(f"    retry {attempt + 1}: {type(e).__name__}: {e}",
                      file=sys.stderr, flush=True)
                continue
            raise
    raise last_err  # pragma: no cover


# ============================================================
# Stage 2: subfield -> scenarios
# ============================================================

def generate_m2_for_subfield(
    caller: ModelCaller,
    discipline: str,
    subfield: dict,
    count: int,
    model: str,
    seed: int,
    start_idx: int = 0,
    taxonomy_context: TaxonomyContext = "name_description_examples",
    max_retries: int = 4,
) -> list[dict]:
    prompt = M2_PROMPT.format(
        discipline=discipline,
        subfield_context=_format_subfield_context(subfield, taxonomy_context),
        k=count,
    )
    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            raw = caller.complete(prompt, model, max_tokens=12000)
            if not raw.strip():
                raise ValueError("empty response")
            payload = _json_from_response(raw)
            validated = ScenarioBatch.model_validate(payload)
            scenarios = [s.model_dump(by_alias=True) for s in validated.scenarios]
            if len(scenarios) != count:
                raise ValueError(f"expected {count} scenarios, got {len(scenarios)}")
            for scenario in validated.scenarios:
                _validate_scenario_spec(scenario.spec)
            for i, scenario in enumerate(scenarios):
                scenario["id"] = f"m2_{subfield['name']}_{seed}_{start_idx + i:03d}"
                scenario["discipline"] = discipline
                scenario["subfield"] = subfield["name"]
                scenario["generation_mode"] = "M2"
                profile = load_taxonomy_profile(discipline, subfield["name"])
                scenario["mechanism_profile"] = profile
                if not scenario.get("baseline_mechanisms"):
                    scenario["baseline_mechanisms"] = [scenario.get("mechanism_tag", "baseline")]
                if not scenario.get("baseline_assumptions"):
                    scenario["baseline_assumptions"] = [
                        "gen0 uses the simplest scenario-consistent response law"
                    ]
                if not scenario.get("scientific_constraints"):
                    scenario["scientific_constraints"] = [
                        "the generated law must remain mathematically finite over its sampled domain"
                    ]
                if not scenario.get("refinement_agenda"):
                    scenario["refinement_agenda"] = [m.get("id") for m in profile.get("domain_mechanisms", [])]
            return scenarios
        except _retryable_errors() as e:
            last_err = e
            if attempt < max_retries:
                print(f"    retry {attempt + 1}: {type(e).__name__}: {e}",
                      file=sys.stderr, flush=True)
                continue
            raise
    raise last_err  # pragma: no cover


# ============================================================
# Stage 3: scenario -> equation
# ============================================================

def derive_equation(
    caller: ModelCaller,
    scenario_text: str,
    spec: dict,
    discipline: str,
    subfield: str,
    model: str,
    dimension_track: str = "fixed_univariate",
    baseline_mechanisms: list[str] | None = None,
    baseline_assumptions: list[str] | None = None,
    scientific_constraints: list[str] | None = None,
    refinement_agenda: list[str] | None = None,
    mechanism_profile: dict | None = None,
    max_retries: int = 3,
) -> dict:
    validated_spec = Spec.model_validate(spec)
    _validate_scenario_spec(validated_spec)
    subfield_line = f"Subfield: {subfield}\n" if subfield else "\n"
    profile = mechanism_profile or load_taxonomy_profile(discipline, subfield)
    evolution_context = (
        f"dimension_track: {dimension_track}\n"
        f"gen0 baseline mechanisms: {', '.join(baseline_mechanisms or []) or '(not recorded)'}\n"
        f"gen0 baseline assumptions: {'; '.join(baseline_assumptions or []) or '(not recorded)'}\n"
        f"scientific constraints: {'; '.join(scientific_constraints or []) or '(not recorded)'}\n"
        f"later refinement agenda: {', '.join(refinement_agenda or []) or '(not recorded)'}\n"
        f"taxonomy mechanism profile:\n{mechanism_menu(profile)}\n"
        "Derive gen0 from baseline mechanisms only. Do not pre-include every agenda mechanism."
    )
    if validated_spec.model_family == "ode":
        prompt = ODE_MODELING_PROMPT.format(
            scenario_text=scenario_text,
            target_symbol=validated_spec.target_symbol,
            target_description=validated_spec.target_description,
            time_symbol=validated_spec.time_symbol,
            time_range=validated_spec.time_range,
            target_state=validated_spec.target_state,
            state_descriptions=_flatten_state_descriptions(
                [state.model_dump() for state in validated_spec.required_dynamic_states]
            ),
            discipline=discipline,
            subfield_line=subfield_line,
            max_ode_states=MAX_ODE_STATES,
            dimension_track=dimension_track,
            evolution_context=evolution_context,
        )
    else:
        prompt = STATIC_MODELING_PROMPT.format(
            scenario_text=scenario_text,
            target_symbol=validated_spec.target_symbol,
            target_description=validated_spec.target_description,
            input_descriptions=_flatten_input_descriptions(
                [item.model_dump() for item in validated_spec.input_symbols]
            ),
            discipline=discipline,
            subfield_line=subfield_line,
            dimension_track=dimension_track,
            evolution_context=evolution_context,
        )

    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            raw = caller.complete(prompt, model, max_tokens=4000)
            if not raw.strip():
                raise ValueError("empty response")
            parsed = json.loads(_strip_code_fence(raw))
            validated = EquationOutput.model_validate(parsed)
            _validate_equation_output(validated, validated_spec)
            result = validated.model_dump()
            if result["dimension_class"] != dimension_track:
                raise ValueError(
                    "equation dimension_class must match scenario dimension_track"
                )
            manifest = dict(result.get("mechanism_manifest") or {})
            manifest.setdefault("baseline_mechanisms", list(baseline_mechanisms or []))
            manifest.setdefault("active_mechanisms", list(baseline_mechanisms or []))
            result["mechanism_manifest"] = manifest
            return result
        except _retryable_errors() as e:
            last_err = e
            if attempt < max_retries:
                print(f"    retry {attempt + 1}: {type(e).__name__}: {e}",
                      file=sys.stderr, flush=True)
                continue
            raise
    raise last_err  # pragma: no cover


# ============================================================
# Output sheet
# ============================================================

def _build_combined_xlsx(
    out_path: Path,
    scenarios: list[dict],
    equations: list[dict],
) -> None:
    if pd is None:
        print("    (pandas not available; skipping xlsx export)", file=sys.stderr)
        return

    eq_by_id = {e["scenario_id"]: e for e in equations if "scenario_id" in e}
    rows = []
    for sc in scenarios:
        spec = sc.get("spec", {})
        eq = eq_by_id.get(sc["id"], {})
        rows.append({
            "id": sc["id"],
            "discipline": sc.get("discipline", ""),
            "subfield": sc.get("subfield", ""),
            "mechanism_tag": sc.get("mechanism_tag", ""),
            "functional_family": sc.get("functional_family", ""),
            "dimension_track": sc.get("dimension_track", "fixed_univariate"),
            "baseline_mechanisms": "; ".join(sc.get("baseline_mechanisms", [])),
            "baseline_assumptions": "; ".join(sc.get("baseline_assumptions", [])),
            "scientific_constraints": "; ".join(sc.get("scientific_constraints", [])),
            "refinement_agenda": "; ".join(sc.get("refinement_agenda", [])),
            "model_family": spec.get("model_family", "static"),
            "scenario_text": sc.get("scenario_text", ""),
            "target_symbol": spec.get("target_symbol", ""),
            "target_description": spec.get("target_description", ""),
            "input_descriptions": _flatten_input_descriptions(spec.get("input_symbols", [])),
            "time_symbol": spec.get("time_symbol", ""),
            "time_range": json.dumps(spec.get("time_range"), ensure_ascii=False),
            "target_state": spec.get("target_state", ""),
            "required_dynamic_states": json.dumps(
                spec.get(
                    "required_dynamic_states",
                    spec.get("dynamic_state_candidates", []),
                ),
                ensure_ascii=False,
            ),
            "expected_behaviors": "; ".join(spec.get("expected_behaviors", [])),
            "forbidden_behaviors": "; ".join(spec.get("forbidden_behaviors", [])),
            "equation_type": eq.get("equation_type", ""),
            "expression": eq.get("expression", ""),
            "symbols": ", ".join(eq.get("symbols", [])),
            "symbol_descriptions": " | ".join(eq.get("symbol_descriptions", [])),
            "symbol_properties": ", ".join(eq.get("symbol_properties", [])),
            "dimension_class": eq.get("dimension_class", ""),
            "mechanism_manifest": json.dumps(eq.get("mechanism_manifest", {}), ensure_ascii=False),
            "ode_system": json.dumps(eq.get("ode_system"), ensure_ascii=False),
            "derivation_notes": eq.get("derivation_notes", ""),
            "equation_error": eq.get("error", ""),
        })

    try:
        pd.DataFrame(rows).to_excel(out_path, index=False)
    except ImportError as exc:
        # pandas is optional and its Excel engine is an independent optional
        # dependency; JSON/JSONL checkpoints remain the source of truth.
        print(f"    (Excel engine unavailable; skipping xlsx export: {exc})", file=sys.stderr)


# ============================================================
# Main pipeline
# ============================================================

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Standalone workflow: subject -> subfield -> scenario -> equation",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--subject", required=True,
                        help="Discipline, e.g. physics, biology, AI, chemistry, economy")
    parser.add_argument("--scenarios", type=int, default=None,
                        help="Total scenarios to generate; required for fixed/generate runs")
    parser.add_argument("--n-subfields", type=int, default=None,
                        help="Fixed/generate: selected subfields. Fixed defaults to taxonomy default_n; generate rolls")
    parser.add_argument("--subfield-source", choices=["fixed", "generate", "extend"],
                        default="fixed",
                        help="fixed: taxonomy slice; generate: fresh LLM partition; extend: LLM review candidates only")
    parser.add_argument("--taxonomy-file",
                        default=str(Path(__file__).resolve().parent / "taxonomy" / "subfield_taxonomy_v1.json"),
                        help="Frozen taxonomy JSON used by fixed/extend modes")
    parser.add_argument("--fixed-equations", default=None,
                        help="Import reviewed Stage-3 equations directly instead of calling the scenario/equation LLMs")
    parser.add_argument("--equation-mode", choices=["auto", "fixed", "generate"], default="auto",
                        help="auto: obey taxonomy fixed-equation policy; fixed: require/import its fixed source; "
                             "generate: run scenario/equation generation even when the taxonomy has a fixed seed source")
    parser.add_argument("--new-subfields", type=int, default=None,
                        help="Number of extension candidates; required with --subfield-source extend")
    parser.add_argument("--extension-output", default=None,
                        help="Candidate JSON path for extend mode; default: taxonomy/candidates/<subject>_...")
    parser.add_argument("--model", default="claude-opus-4-7",
                        help="Model for subfield and scenario generation")
    parser.add_argument("--equation-model", default=None,
                        help="Model for equation generation; default is --model")
    parser.add_argument("--provider", choices=["anthropic", "openrouter"],
                        default="anthropic",
                        help="Model API protocol. openrouter uses its OpenAI-compatible endpoint")
    parser.add_argument("--base-url", default=None,
                        help="Provider base URL. Defaults to provider-specific environment value")
    parser.add_argument("--auth-source", choices=["auto", "api_key", "auth_token"],
                        default="auto",
                        help="auto prefers ANTHROPIC_API_KEY then ANTHROPIC_AUTH_TOKEN")
    parser.add_argument("--taxonomy-context",
                        choices=["name", "name_description", "name_description_examples"],
                        default="name_description_examples",
                        help="How much subfield context to include in scenario prompt")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--batch-size", type=int, default=10,
                        help="Max scenarios requested per scenario API call")
    parser.add_argument("--output-dir", default=None,
                        help="Base output dir")
    parser.add_argument("--run-name", default=None,
                        help="Fixed output folder name")
    parser.add_argument("--resume", action="store_true",
                        help="continue an existing --run-name from saved JSONL checkpoints")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print planned quotas without API calls")
    args = parser.parse_args()

    if args.resume and not args.run_name:
        raise SystemExit("--resume requires an explicit --run-name.")
    if args.resume and args.subfield_source == "extend":
        raise SystemExit("--resume applies to fixed/generate benchmark runs, not extend mode.")

    source: SubfieldSource = args.subfield_source
    taxonomy_path = Path(args.taxonomy_file).expanduser().resolve()
    equation_model = args.equation_model or args.model

    # A taxonomy subject may declare a reviewed fixed-equation source.  Such
    # records already are Stage-3 gen0 equations, so they use the common
    # checkpoint layout without making redundant Stage-2/3 API calls.
    if args.equation_mode == "generate" and args.fixed_equations:
        raise SystemExit("--equation-mode generate cannot be combined with --fixed-equations.")
    fixed_source_value = args.fixed_equations
    fixed_equation_count: int | None = None
    if args.equation_mode != "generate" and fixed_source_value is None and source == "fixed":
        taxonomy_for_mode, _ = _load_taxonomy_subject(taxonomy_path, args.subject)
        subject_entry = taxonomy_for_mode["subjects"][args.subject]
        if subject_entry.get("equation_mode") == "fixed":
            fixed_source_value = subject_entry.get("fixed_equation_source")
            fixed_equation_count = subject_entry.get("fixed_equation_count")
    if args.equation_mode == "fixed" and not fixed_source_value:
        raise SystemExit(
            "--equation-mode fixed requires --fixed-equations or a taxonomy fixed_equation_source."
        )
    if fixed_source_value:
        if source != "fixed":
            raise SystemExit("--fixed-equations requires --subfield-source fixed.")
        if args.resume:
            raise SystemExit("--resume is not supported for fixed equation imports; use a new --run-name.")
        source_path = Path(fixed_source_value).expanduser()
        if not source_path.is_absolute():
            repo_relative = Path(__file__).resolve().parent / source_path
            source_path = repo_relative if repo_relative.exists() else source_path.resolve()
        if args.dry_run:
            print(f"[dry-run] Would import fixed equations from {source_path}.", file=sys.stderr)
            return
        _run_fixed_equation_import(args, taxonomy_path, source_path, fixed_equation_count)
        return

    rng = random.Random(args.seed)
    fixed_subfields: list[dict] | None = None
    n_subfields = 0
    quotas: list[int] = []
    rolled = False

    if source == "extend":
        if args.new_subfields is None or args.new_subfields < 1:
            raise SystemExit("--new-subfields must be a positive integer with --subfield-source extend.")
        # Validate the frozen taxonomy before making a paid extension request.
        _, existing_subfields = _load_taxonomy_subject(taxonomy_path, args.subject)
        n_subfields = args.new_subfields
    else:
        if args.scenarios is None or args.scenarios <= 0:
            raise SystemExit("--scenarios must be positive with fixed or generate mode.")
        if source == "fixed":
            fixed_subfields, n_subfields = _resolve_fixed_subfields(
                taxonomy_path, args.subject, args.n_subfields,
            )
        else:
            rolled = args.n_subfields is None
            n_subfields = (roll_subfield_count(args.scenarios, rng)
                           if rolled else max(1, args.n_subfields))
        if n_subfields > args.scenarios:
            raise SystemExit(
                f"Selected {n_subfields} subfields but only {args.scenarios} scenarios. "
                "Increase --scenarios or reduce --n-subfields."
            )
        quotas = _allocate_counts(args.scenarios, n_subfields)

    taxonomy_sha256 = (
        _sha256_file(taxonomy_path) if source in ("fixed", "extend") else None
    )

    print("=" * 72, file=sys.stderr)
    title = "Subfield Extension" if source == "extend" else "Standalone Auto Workflow"
    print(f"{title} | subject={args.subject}", file=sys.stderr)
    if source != "extend":
        print(f"  scenarios        : {args.scenarios}", file=sys.stderr)
    print(f"  subfield_source  : {source}", file=sys.stderr)
    if source in ("fixed", "extend"):
        print(f"  taxonomy_file    : {taxonomy_path}", file=sys.stderr)
    if source == "extend":
        print(f"  candidates       : {n_subfields}", file=sys.stderr)
        print(f"  existing         : {len(existing_subfields)} frozen subfields", file=sys.stderr)
    else:
        selection = (f"rolled from seed {args.seed}" if rolled else
                     "taxonomy order" if source == "fixed" else "explicit")
        print(f"  subfields        : {n_subfields} ({selection})", file=sys.stderr)
        print(f"  quotas           : {quotas} (sum={sum(quotas)})", file=sys.stderr)
    print(f"  models           : scenario={args.model} equation={equation_model}",
          file=sys.stderr)
    print(f"  taxonomy_context : {args.taxonomy_context}", file=sys.stderr)
    if source != "extend":
        print(f"  resume           : {args.resume}", file=sys.stderr)
    print("=" * 72, file=sys.stderr)

    if args.dry_run:
        print("[dry-run] No API calls made.", file=sys.stderr)
        return

    provider: Provider = args.provider
    if provider == "openrouter":
        if args.auth_source != "auto":
            print("    note: --auth-source is ignored with --provider openrouter", file=sys.stderr)
        openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise SystemExit("Missing OPENROUTER_API_KEY.")
        base_url = args.base_url or os.environ.get("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"
        caller = ModelCaller(
            "openrouter",
            openrouter_api_key=openrouter_api_key.strip(),
            openrouter_base_url=base_url.strip(),
        )
        resolved_auth_source = "openrouter_api_key"
    else:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        auth_token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
        base_url = args.base_url or os.environ.get("ANTHROPIC_BASE_URL") or "https://code.ppchat.vip/"
        client_kwargs, resolved_auth_source = _build_client_kwargs(
            api_key=api_key,
            auth_token=auth_token,
            base_url=base_url,
            auth_source=args.auth_source,
        )
        caller = ModelCaller("anthropic", anthropic_client=anthropic.Anthropic(**client_kwargs))

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    if source == "extend":
        default_candidate = (
            Path(__file__).resolve().parent / "taxonomy" / "candidates" /
            f"{args.subject}_extensions_{timestamp}.json"
        )
        candidate_path = (Path(args.extension_output).expanduser()
                          if args.extension_output else default_candidate)
        if candidate_path.exists():
            raise SystemExit(
                f"Extension output already exists: {candidate_path}. "
                "Choose a new --extension-output path."
            )
        print(f"\n[extension] Proposing {args.new_subfields} candidate subfields...",
              file=sys.stderr, flush=True)
        candidates = propose_subfield_extensions(
            caller=caller,
            discipline=args.subject,
            existing_subfields=existing_subfields,
            n=args.new_subfields,
            model=args.model,
        )
        source_taxonomy, _ = _load_taxonomy_subject(taxonomy_path, args.subject)
        _write_json(candidate_path, {
            "candidate_schema_version": "1.0",
            "status": "pending_human_review",
            "discipline": args.subject,
            "source_taxonomy_file": str(taxonomy_path),
            "source_taxonomy_schema_version": source_taxonomy.get("schema_version"),
            "model": args.model,
            "provider": provider,
            "seed": args.seed,
            "timestamp": timestamp,
            "existing_subfield_names": [sf["name"] for sf in existing_subfields],
            "candidates": candidates,
            "review_instruction": (
                "Review candidates for curriculum validity, overlap, and comparable "
                "granularity. Append approved entries manually to a new taxonomy version; "
                "do not modify or reorder frozen entries."
            ),
        })
        print(f"    -> {len(candidates)} candidates written to {candidate_path}",
              file=sys.stderr)
        print("    -> No scenarios or equations were generated; human review is required.",
              file=sys.stderr)
        return

    base_out = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent / "outputs"
    run_name = args.run_name or f"{args.subject}_{timestamp}"
    scenarios_dir = base_out / "Scenarios" / run_name
    equations_dir = base_out / "Equations" / run_name

    subfields_path = scenarios_dir / "subfields.json"
    scenarios_path = scenarios_dir / "scenarios.jsonl"
    equations_path = equations_dir / "equations.jsonl"
    equation_failures_path = equations_dir / "equation_failures.jsonl"
    combined_xlsx = equations_dir / "pipeline.xlsx"
    meta_path = equations_dir / "run_meta.json"
    progress_path = equations_dir / "progress.json"

    resume_config = {
        "subject": args.subject,
        "requested_scenarios": args.scenarios,
        "n_subfields_requested": n_subfields,
        "subfields_rolled": rolled,
        "subfield_source": source,
        "taxonomy_file": str(taxonomy_path) if source == "fixed" else None,
        "taxonomy_sha256": taxonomy_sha256 if source == "fixed" else None,
        "taxonomy_slice_policy": (
            "first_n_in_listed_order" if source == "fixed" else None
        ),
        "seed": args.seed,
        "provider": provider,
        "scenario_model": args.model,
        "equation_model": equation_model,
        "batch_size": args.batch_size,
        "taxonomy_context": args.taxonomy_context,
        "base_url": base_url,
        "auth_source": resolved_auth_source,
    }

    checkpoint_paths = [
        subfields_path, scenarios_path, equations_path, equation_failures_path,
        meta_path, progress_path,
    ]
    existing_checkpoints = [path for path in checkpoint_paths if path.exists()]
    if args.resume:
        if not meta_path.exists():
            raise SystemExit(
                f"Cannot resume run '{run_name}': missing {meta_path}."
            )
        saved_meta = _load_json_object(meta_path)
        _assert_resume_config(saved_meta, resume_config, meta_path)
        meta = dict(saved_meta)
        meta.update({
            "status": "running",
            "resumed_at": timestamp,
            "resume_count": int(saved_meta.get("resume_count", 0)) + 1,
        })
        print(f"\n[resume] Validated checkpoint metadata for '{run_name}'.",
              file=sys.stderr)
    else:
        if existing_checkpoints:
            listed = "\n  ".join(str(path) for path in existing_checkpoints)
            raise SystemExit(
                f"Run '{run_name}' already has checkpoint files:\n  {listed}\n"
                "Use --resume with the identical command, or choose a new --run-name."
            )
        meta = dict(resume_config)
        meta.update({
            "timestamp": timestamp,
            "resume_count": 0,
        })

    scenarios_dir.mkdir(parents=True, exist_ok=True)
    equations_dir.mkdir(parents=True, exist_ok=True)
    meta.update({
        "timestamp": meta.get("timestamp", timestamp),
        "run_name": run_name,
        "scenarios_dir": str(scenarios_dir),
        "equations_dir": str(equations_dir),
        "status": "running",
    })
    _write_json(meta_path, meta)

    try:
        if args.resume and subfields_path.exists():
            checkpoint = _load_json_object(subfields_path)
            if checkpoint.get("discipline") != args.subject:
                raise SystemExit(
                    f"Cannot resume: {subfields_path} belongs to "
                    f"{checkpoint.get('discipline')!r}, not {args.subject!r}."
                )
            if checkpoint.get("subfield_source") != source:
                raise SystemExit(
                    f"Cannot resume: subfield source in {subfields_path} changed."
                )
            subfields = checkpoint.get("subfields")
            if not isinstance(subfields, list) or not subfields:
                raise SystemExit(f"Cannot resume: no saved subfields in {subfields_path}.")
            if source == "fixed":
                expected_names = [sf["name"] for sf in (fixed_subfields or [])]
                saved_names = [sf.get("name") for sf in subfields]
                if saved_names != expected_names:
                    raise SystemExit(
                        "Cannot resume: saved fixed subfield slice does not match taxonomy."
                    )
            n_subfields = len(subfields)
            quotas = _allocate_counts(args.scenarios, n_subfields)
            print(f"\n[1/3] Resuming with {len(subfields)} saved subfields...",
                  file=sys.stderr, flush=True)
        elif source == "fixed":
            subfields = fixed_subfields or []
            print(f"\n[1/3] Loading {len(subfields)} fixed subfields from taxonomy...",
                  file=sys.stderr, flush=True)
        else:
            print(f"\n[1/3] Expanding '{args.subject}' into {n_subfields} subfields...",
                  file=sys.stderr, flush=True)
            subfields = expand_discipline(
                caller=caller,
                discipline=args.subject,
                n=n_subfields,
                model=args.model,
            )
            if len(subfields) != n_subfields:
                print(f"    note: model returned {len(subfields)} subfields "
                      f"(requested {n_subfields}); re-allocating quotas.",
                      file=sys.stderr)
                n_subfields = len(subfields)
                quotas = _allocate_counts(args.scenarios, n_subfields)
        if not (args.resume and subfields_path.exists()):
            _write_json(subfields_path, {
                "discipline": args.subject,
                "subfield_source": source,
                "taxonomy_file": str(taxonomy_path) if source == "fixed" else None,
                "taxonomy_sha256": taxonomy_sha256 if source == "fixed" else None,
                "subfields": subfields,
            })
        print(f"    -> {len(subfields)} subfields written to {subfields_path.name}",
              file=sys.stderr)

        print(f"\n[2/3] Generating {args.scenarios} scenarios...",
              file=sys.stderr, flush=True)
        all_scenarios = _load_jsonl(scenarios_path) if args.resume else []
        valid_subfields = {sf["name"] for sf in subfields}
        seen_ids: set[str] = set()
        for scenario in all_scenarios:
            scenario_id = scenario.get("id")
            if not isinstance(scenario_id, str) or not scenario_id:
                raise SystemExit(f"Cannot resume: scenario without an id in {scenarios_path}.")
            if scenario_id in seen_ids:
                raise SystemExit(
                    f"Cannot resume: duplicate scenario id '{scenario_id}' in {scenarios_path}."
                )
            seen_ids.add(scenario_id)
            if scenario.get("discipline") != args.subject:
                raise SystemExit(
                    f"Cannot resume: scenario '{scenario_id}' has a different discipline."
                )
            if scenario.get("subfield") not in valid_subfields:
                raise SystemExit(
                    f"Cannot resume: scenario '{scenario_id}' has unknown subfield "
                    f"'{scenario.get('subfield')}'."
                )

        if args.resume:
            print(f"    checkpoint contains {len(all_scenarios)} scenario(s).",
                  file=sys.stderr)
        paired = list(zip(subfields, quotas))
        rng.shuffle(paired)

        for sf, count in paired:
            existing_count = sum(
                1 for scenario in all_scenarios
                if scenario.get("subfield") == sf["name"]
            )
            if existing_count > count:
                raise SystemExit(
                    f"Cannot resume: subfield '{sf['name']}' already has {existing_count} "
                    f"scenarios, above its quota {count}."
                )
            missing = count - existing_count
            if missing <= 0:
                if args.resume:
                    print(f"    [{sf['name']}] complete ({existing_count}/{count}); skipping.",
                          file=sys.stderr)
                continue
            offset = _next_scenario_index(all_scenarios, sf["name"], args.seed)
            for chunk in _chunk_counts(missing, args.batch_size):
                print(f"    [{sf['name']}] generating {chunk} scenario(s)...",
                      file=sys.stderr, flush=True)
                items = generate_m2_for_subfield(
                    caller=caller,
                    discipline=args.subject,
                    subfield=sf,
                    count=chunk,
                    model=args.model,
                    seed=args.seed,
                    start_idx=offset,
                    taxonomy_context=args.taxonomy_context,
                )
                for item in items:
                    all_scenarios.append(item)
                    _append_jsonl(scenarios_path, item)
                offset += chunk
                _write_json(progress_path, {
                    "stage": "scenarios",
                    "n_scenarios_generated": len(all_scenarios),
                    "last_subfield": sf["name"],
                    "status": "running",
                })

        print(f"    -> {len(all_scenarios)} scenarios written to {scenarios_path.name}",
              file=sys.stderr)

        print(f"\n[3/3] Deriving equations for {len(all_scenarios)} scenarios...",
              file=sys.stderr, flush=True)
        saved_equations = _load_jsonl(equations_path) if args.resume else []
        equations_by_id: dict[str, dict] = {}
        legacy_failures: list[dict] = []
        for equation in saved_equations:
            scenario_id = equation.get("scenario_id")
            if not isinstance(scenario_id, str) or not scenario_id:
                raise SystemExit(f"Cannot resume: equation without scenario_id in {equations_path}.")
            if "expression" in equation:
                if scenario_id in equations_by_id:
                    raise SystemExit(
                        f"Cannot resume: duplicate successful equation '{scenario_id}'."
                    )
                equations_by_id[scenario_id] = equation
            else:
                legacy_failures.append(equation)
        if legacy_failures:
            known_failure_keys = {
                (row.get("scenario_id"), row.get("error"))
                for row in _load_jsonl(equation_failures_path)
            }
            for failure in legacy_failures:
                key = (failure.get("scenario_id"), failure.get("error"))
                if key not in known_failure_keys:
                    _append_jsonl(equation_failures_path, failure)
                    known_failure_keys.add(key)
            _write_jsonl(equations_path, list(equations_by_id.values()))

        if args.resume:
            print(f"    checkpoint contains {len(equations_by_id)} successful equation(s).",
                  file=sys.stderr)
        failures_this_attempt = 0
        for i, sc in enumerate(all_scenarios, 1):
            spec = sc.get("spec", {})
            scenario_id = sc["id"]
            if scenario_id in equations_by_id:
                print(f"    [{i}/{len(all_scenarios)}] {scenario_id}: already complete; skipping.",
                      file=sys.stderr, flush=True)
                continue
            print(f"    [{i}/{len(all_scenarios)}] {scenario_id}...",
                  file=sys.stderr, flush=True)
            try:
                eq = derive_equation(
                    caller=caller,
                    scenario_text=sc.get("scenario_text", ""),
                    spec=spec,
                    discipline=sc.get("discipline", args.subject),
                    subfield=sc.get("subfield", ""),
                    model=equation_model,
                    dimension_track=sc.get("dimension_track", "fixed_univariate"),
                    baseline_mechanisms=sc.get("baseline_mechanisms", []),
                    baseline_assumptions=sc.get("baseline_assumptions", []),
                    scientific_constraints=sc.get("scientific_constraints", []),
                    refinement_agenda=sc.get("refinement_agenda", []),
                    mechanism_profile=sc.get("mechanism_profile") or None,
                )
                eq["scenario_id"] = scenario_id
                eq["scenario_text"] = sc.get("scenario_text", "")
                eq["discipline"] = sc.get("discipline", args.subject)
                eq["subfield"] = sc.get("subfield", "")
                eq["model_family"] = spec.get("model_family", "static")
                eq["dimension_track"] = sc.get("dimension_track", "fixed_univariate")
                eq["baseline_mechanisms"] = sc.get("baseline_mechanisms", [])
                eq["baseline_assumptions"] = sc.get("baseline_assumptions", [])
                eq["scientific_constraints"] = sc.get("scientific_constraints", [])
                eq["refinement_agenda"] = sc.get("refinement_agenda", [])
                eq["mechanism_profile"] = sc.get("mechanism_profile", {})
            except Exception as e:
                print(f"      FAILED: {type(e).__name__}: {e}",
                      file=sys.stderr, flush=True)
                eq = {
                    "scenario_id": scenario_id,
                    "discipline": sc.get("discipline", args.subject),
                    "subfield": sc.get("subfield", ""),
                    "error": f"{type(e).__name__}: {e}",
                    "attempted_at": datetime.now().isoformat(timespec="seconds"),
                }
                failures_this_attempt += 1
                _append_jsonl(equation_failures_path, eq)
            else:
                equations_by_id[scenario_id] = eq
                _append_jsonl(equations_path, eq)
            _write_json(progress_path, {
                "stage": "equations",
                "n_scenarios_generated": len(all_scenarios),
                "n_equations_ok": len(equations_by_id),
                "n_equations_remaining": len(all_scenarios) - len(equations_by_id),
                "n_equation_failures_this_attempt": failures_this_attempt,
                "last_scenario_id": scenario_id,
                "status": "running",
            })

        equations = [
            equations_by_id[scenario["id"]]
            for scenario in all_scenarios
            if scenario["id"] in equations_by_id
        ]
        _write_jsonl(equations_path, equations)
        n_ok = len(equations)
        n_failed = len(all_scenarios) - n_ok
        _build_combined_xlsx(combined_xlsx, all_scenarios, equations)

        meta.update({
            "status": "complete" if n_failed == 0 else "complete_with_failures",
            "n_subfields": len(subfields),
            "subfield_names": [sf["name"] for sf in subfields],
            "quotas": {sf["name"]: q for sf, q in zip(subfields, quotas)},
            "n_scenarios_generated": len(all_scenarios),
            "n_equations_ok": n_ok,
            "n_equations_failed": n_failed,
        })
        _write_json(meta_path, meta)
        _write_json(progress_path, {
            "stage": "complete" if n_failed == 0 else "complete_with_failures",
            "n_scenarios_generated": len(all_scenarios),
            "n_equations_ok": n_ok,
            "n_equations_failed": n_failed,
            "status": "complete" if n_failed == 0 else "complete_with_failures",
        })

        print("\n" + "=" * 72, file=sys.stderr)
        print("Done. Outputs:", file=sys.stderr)
        print(f"  Scenarios : {scenarios_dir}", file=sys.stderr)
        print(f"    subfields.json  ({len(subfields)} subfields)", file=sys.stderr)
        print(f"    scenarios.jsonl ({len(all_scenarios)} scenarios)", file=sys.stderr)
        print(f"  Equations : {equations_dir}", file=sys.stderr)
        print(f"    equations.jsonl ({n_ok} ok / {len(all_scenarios)} requested)", file=sys.stderr)
        if n_failed:
            print(f"    equation_failures.jsonl ({n_failed} pending; rerun with --resume)",
                  file=sys.stderr)
        print("    pipeline.xlsx   (joined review sheet)", file=sys.stderr)
        print("    run_meta.json", file=sys.stderr)
        print("=" * 72, file=sys.stderr)

    except Exception as e:
        meta.update({
            "status": "failed",
            "error": f"{type(e).__name__}: {e}",
        })
        _write_json(meta_path, meta)
        _write_json(progress_path, {
            "stage": "failed",
            "status": "failed",
            "error": f"{type(e).__name__}: {e}",
        })
        hint = _failure_hint(e, args.model, base_url, resolved_auth_source, provider)
        if hint:
            print("\n" + hint, file=sys.stderr)
        print("Generation failed. Partial outputs retained in:", file=sys.stderr)
        print(f"  Scenarios : {scenarios_dir}", file=sys.stderr)
        print(f"  Equations : {equations_dir}",
              file=sys.stderr)
        raise


if __name__ == "__main__":
    main()
