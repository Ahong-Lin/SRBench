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
growing in complexity. After every step the dependent variable, independent
variables, and parameters are written out explicitly — same spirit as the
original equation record.

It reuses `Scenario-equation/generate_equations.py` (schema + helpers) so the
equation format stays identical across the pipeline.

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
import os
import random
import re
import sys
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel

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

class EvolvedEquation(BaseModel):
    target_symbol: str
    expression: str
    symbols: list[str]
    symbol_descriptions: list[str]
    symbol_properties: list[str]
    new_symbol_range_suggestions: dict[str, str]
    derivation_notes: str
    change_summary: str


class EvolvedEquationValidationError(ValueError):
    """Raised when an evolved equation is structurally inconsistent."""


# ============================================================
# Prompts
# ============================================================

_RULES = """\
REQUIREMENTS:
1. Write the equation in Python/sympy syntax. Use ** for power, and
   sqrt(), sin(), cos(), exp(), log(), Abs(), tanh(), etc. Use sympy Function
   notation for functions of an independent variable, e.g. x(t).
2. Use descriptive named parameters (omega0, gamma, alpha, k_B, ...). Do NOT use
   floating-point literals for physical constants.
3. For an explicit relation, "expression" is the RHS such that
   {target_symbol} = expression.
   For an ODE, "expression" is f(inputs, parameters) where {target_symbol} is the
   highest derivative described.
   For an implicit/transcendental relation, "expression" is the FULL f(...) such
   that f(...) = 0 (never just "0").
4. Keep every symbol that still appears in the new equation, and add entries for
   any NEW variables/parameters you introduce.
5. If you introduce any NEW symbols in this step, you MUST include a suggested
   numeric sampling range for each one in "new_symbol_range_suggestions". Use
   short interval strings such as "[1e-4, 1e-2]" or "[0, 10]" and mention key
   constraints like positivity when helpful.

symbol_properties uses one letter per symbol, aligned with "symbols":
  "O" = the output/target (dependent variable),
  "V" = an input variable (independent variable),
  "P" = a parameter/constant.

OUTPUT FORMAT — return a SINGLE JSON object, nothing else:
{{
  "target_symbol": "{target_symbol}",
  "expression": "<sympy expression string>",
  "symbols": ["<target>", "<var1>", "<param1>", ...],
  "symbol_descriptions": ["<desc>", "<desc>", ...],
  "symbol_properties": ["O", "V", "P", ...],
  "new_symbol_range_suggestions": {{"<new_symbol>": "<suggested range>", ...}},
  "derivation_notes": "<1-2 sentences on the physical law / reasoning behind the NEW equation>",
  "change_summary": "<1-2 sentences stating exactly WHAT you changed in this step and WHY it makes the model richer>"
}}
The first character of your response must be `{{` and the last must be `}}`.
Do NOT wrap in markdown fences. Do NOT add any prose before or after the JSON.
"""

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

The following are only ILLUSTRATIONS of the KINDS of assumption-changes that
exist — do NOT pick from this list mechanically; choose whatever is genuinely
appropriate for the system at hand:
  - a parameter assumed constant now varies with a relevant state variable,
  - a small/neglected effect that actually matters here is now retained,
  - a linear response becomes nonlinear where the physics demands it,
  - an idealization is dropped (e.g. inviscid -> viscous, dilute -> concentrated,
    isothermal -> with heat exchange, point-mass -> finite-size).
The successor equation must be genuinely different and generally MORE complex
than the current one. Introduce any new named parameters/variables the new
assumption requires. In "change_summary", name the assumption you changed AND
why it is the natural next refinement for THIS system.

""" + _RULES

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

The following are only ILLUSTRATIONS of the KINDS of effects that can be added —
do NOT pick from this list mechanically; choose whatever the physics of THIS
system actually calls for:
  damping/dissipation, an external driving/forcing term, coupling to another
  quantity, a nonlinear correction, a saturation term, a source/sink, a spatial
  or memory (history-dependent) term, a feedback term.
Introduce any new named parameters/variables the added term needs. In
"change_summary", name the physical effect the new term represents AND why it is
the natural missing piece for THIS system.

""" + _RULES


# ============================================================
# Helpers
# ============================================================

def _role_name(letter: str) -> str:
    return {"O": "output", "V": "variable", "P": "parameter"}.get(letter, "?")


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


def _normalize_and_validate_evolved(
    current: dict,
    candidate: dict,
) -> tuple[dict, list[str]]:
    """Validate symbol bookkeeping and gently normalize obvious role mistakes."""
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

    invalid_roles = [p for p in properties if p not in {"O", "V", "P"}]
    if invalid_roles:
        raise EvolvedEquationValidationError(
            f"invalid symbol_properties found: {sorted(set(invalid_roles))}"
        )

    o_symbols = [sym for sym, prop in zip(symbols, properties) if prop == "O"]
    if o_symbols != [target_symbol]:
        raise EvolvedEquationValidationError(
            f"exactly one 'O' is required and it must be '{target_symbol}', got {o_symbols}"
        )

    declared = set(symbols)
    used_names, custom_called = _extract_expression_names(expression, declared)
    unknown = sorted(used_names - declared)
    if unknown:
        raise EvolvedEquationValidationError(
            "expression uses undeclared symbols: " + ", ".join(unknown)
        )

    unused = sorted(sym for sym in symbols if sym != target_symbol and sym not in used_names)
    if unused:
        raise EvolvedEquationValidationError(
            "symbols declared but not used in expression: " + ", ".join(unused)
        )

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

    changes: list[str] = []
    normalized = properties[:]
    for i, sym in enumerate(symbols):
        new_role = properties[i]
        if sym == target_symbol:
            new_role = "O"
        if sym in custom_called and new_role == "P":
            new_role = "V"
        if new_role != properties[i]:
            changes.append(f"{sym}: {properties[i]} -> {new_role}")
        normalized[i] = new_role

    out["symbol_properties"] = normalized
    return out, changes


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


def _split_roles(eq: dict) -> dict:
    """Pull dependent / independent / parameters out of symbols+properties."""
    syms = eq.get("symbols", [])
    descs = eq.get("symbol_descriptions", [])
    props = eq.get("symbol_properties", [])
    dependent, independent, parameters = None, [], []
    for i, sym in enumerate(syms):
        role = props[i] if i < len(props) else "?"
        desc = descs[i] if i < len(descs) else ""
        entry = {"symbol": sym, "description": desc}
        if role == "O":
            dependent = entry
        elif role == "V":
            independent.append(entry)
        elif role == "P":
            parameters.append(entry)
    return {
        "dependent_variable": dependent,
        "independent_variables": independent,
        "parameters": parameters,
    }


def _print_equation(eq: dict, prefix: str = "    ") -> None:
    roles = _split_roles(eq)
    dep = roles["dependent_variable"]
    indep = roles["independent_variables"]
    params = roles["parameters"]
    print(f"{prefix}{eq.get('target_symbol','?')} = {eq.get('expression','?')}",
          file=sys.stderr)
    if dep:
        print(f"{prefix}  dependent  : {dep['symbol']} — {dep['description']}",
              file=sys.stderr)
    if indep:
        names = ", ".join(s["symbol"] for s in indep)
        print(f"{prefix}  independent: {names}", file=sys.stderr)
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
    max_retries: int = 3,
) -> dict:
    template = CHANGE_ASSUMPTION_PROMPT if operation == "change_assumption" else ADD_TERM_PROMPT

    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            prompt = template.format(
                discipline=discipline,
                scenario_text=scenario_text or "(no scenario text recorded)",
                target_symbol=current.get("target_symbol", "y"),
                expression=current.get("expression", ""),
                symbol_table=_symbol_table(current),
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
        "target_symbol": eq.get("target_symbol", ""),
        "expression": eq.get("expression", ""),
        "symbols": eq.get("symbols", []),
        "symbol_descriptions": eq.get("symbol_descriptions", []),
        "symbol_properties": eq.get("symbol_properties", []),
        "new_symbol_range_suggestions": eq.get("new_symbol_range_suggestions", {}),
        "derivation_notes": eq.get("derivation_notes", ""),
        "change_summary": eq.get("change_summary", ""),
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
        params = ", ".join(s["symbol"] for s in rec.get("parameters", []))
        dep = rec.get("dependent_variable") or {}
        nov = rec.get("novelty") or {}
        rows.append({
            "generation": rec["generation"],
            "operation": rec["operation"],
            "target_symbol": rec["target_symbol"],
            "expression": rec["expression"],
            "dependent_variable": dep.get("symbol", ""),
            "independent_variables": indep,
            "parameters": params,
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
    base = _select_equation(usable, args.id, args.interactive)
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
