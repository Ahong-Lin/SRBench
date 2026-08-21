"""
Stage 6a — Data-Generation SPEC agent (official claude-agent-sdk version).
=========================================================================

Take ONE evolved-equation record (the output of `equation_evolve.py`) and decide
*how to turn it into data points* — WITHOUT computing any data here. The output is
a `DataGenSpec`: a plan that Stage 6b (pure numpy/scipy) executes deterministically.

Why an agent with tools (not a one-shot classifier)
---------------------------------------------------
The evolved `expression` is usually correct, but the role tags it ships with
(`symbol_properties`: O / V / P) and the implied equation *type* are often WRONG.
Getting those right is a math-reasoning task, so we give the model a sympy
"microscope" and let it reason -> call sympy -> check -> correct:

  analyze_expression  — parse the expression and report HARD FACTS:
                        free symbols, derivatives (and orders), integral kernels,
                        applied functions f(x), explicit solvability for the target.
  check_substitution  — plug in candidate parameter values + a test point and
                        report finite / real / complex / NaN.
  emit_data_gen_spec  — terminal tool: the agent calls it exactly once with the
                        finished plan. Calling it ends the run.

The default ``anthropic`` provider runs on the OFFICIAL `claude_agent_sdk` (the
`@tool` + `create_sdk_mcp_server` in-process MCP pattern). The SDK spawns the
`claude` CLI under the hood. ``--provider openrouter`` instead runs the same
tool loop in Python over OpenRouter's OpenAI-compatible tool-calling protocol;
that mode does not require the Claude CLI.

Requirements
------------
  * Python >= 3.10 (SDK requirement). Use the `srbench-agent` conda env.
  * `claude` CLI installed (npm i -g @anthropic-ai/claude-code), path passed via
    --cli-path or auto-detected at ~/.npm-global/bin/claude.
  * Env: ANTHROPIC_AUTH_TOKEN (+ ANTHROPIC_BASE_URL, defaults to code.ppchat.vip).

Usage
-----
    python data_spec_agent_sdk.py --demo
    python data_spec_agent_sdk.py --input evolution_xxx.jsonl --output specs.jsonl
    python data_spec_agent_sdk.py --input f.jsonl --id m1_physics_42 --generation 5
"""

from __future__ import annotations

import argparse
import asyncio
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from model_provider import ModelRequestError, build_model_caller

try:
    from claude_agent_sdk import (
        tool,
        create_sdk_mcp_server,
        query,
        ClaudeAgentOptions,
        AssistantMessage,
        TextBlock,
        ToolUseBlock,
        ResultMessage,
    )
    _SDK_IMPORT_ERROR = None
except ModuleNotFoundError as e:
    tool = create_sdk_mcp_server = query = ClaudeAgentOptions = None
    AssistantMessage = TextBlock = ToolUseBlock = ResultMessage = None
    _SDK_IMPORT_ERROR = e


# ============================================================
# DataGenSpec — the contract between this agent (6a) and the
# deterministic generator (6b). Fields map onto the existing
# integrators' CLI (integrate_ode / integrate_system / ...).
# ============================================================

class IndepVar(BaseModel):
    symbol: str
    range: list[float] = Field(..., description="[low, high] sampling interval")
    n_points: int = 200
    scale: str = "linear"  # "linear" | "log"


class FixedParam(BaseModel):
    symbol: str
    value: float


class DataGenSpec(BaseModel):
    # ---- classification (re-derived for static records; inherited for typed ODEs) ----
    equation_type: str = Field(
        ...,
        description="explicit | implicit | ode1 | ode_higher | ode_system | "
                    "delay_differential | integro_diff | unsupported",
    )
    integrator: str = Field(
        ...,
        description="evaluate_explicit | root_solve_implicit | integrate_ode | "
                    "integrate_system | integrate_dde | integrate_basset | unsupported",
    )

    # ---- roles, re-derived ----
    dependent_variable: str
    independent_variables: list[IndepVar]
    parameters: list[FixedParam]

    # For a coupled ODE, `dependent_variable` remains the integrated state while
    # `benchmark_output` is the derivative label that symbolic regression learns.
    benchmark_output: str | None = Field(
        default=None,
        description="For typed ODEs, the upstream O target symbol such as dv_dt. "
                    "This is the symbolic-regression label, not an integrated state.",
    )
    benchmark_target_state: str | None = Field(
        default=None,
        description="The state whose RHS defines benchmark_output, such as v for dv_dt.",
    )
    observed_variables: list[str] = Field(
        default_factory=list,
        description="Columns exposed to symbolic regression, including time and observed states.",
    )

    # ---- what 6b needs to actually run ----
    rhs_for_integrator: str = Field(
        ...,
        description="The cleaned RHS to hand the integrator. For an ODE this is "
                    "f(...) in dy/dt = f(...); for explicit it is the RHS of "
                    "y = RHS; for implicit it is g(...) in g(...) = 0.",
    )
    state_variables: list[str] = Field(
        default_factory=list,
        description="For ode_system/ode_higher: ordered state variables after "
                    "reduction to first order (e.g. ['x','v']). Empty otherwise.",
    )
    state_rhs: list[str] = Field(
        default_factory=list,
        description="For ode_system/ode_higher: d(state_i)/dt expressions, aligned "
                    "with state_variables. Empty otherwise.",
    )
    initial_conditions: dict[str, float] = Field(default_factory=dict)

    # ---- data realism ----
    noise: float = Field(
        0.0,
        description="Absolute Gaussian noise std on the benchmark output for typed ODEs, "
                    "or on the dependent variable otherwise. This is "
                    "the 'visibility yardstick': every term must move the data by "
                    ">= k*noise somewhere in the sampled region (see excitation_report).",
    )
    sanity_expectations: list[str] = Field(
        default_factory=list,
        description="Checkable expectations (e.g. 'monotone increasing', 'bounded', "
                    "'approaches a finite asymptote') used by Stage 6c to validate.",
    )

    # ---- excitation: is every term (esp. the newest) visible above the noise? ----
    excitation_ok: bool = Field(
        True,
        description="True if every term — and the new term vs the parent — reaches "
                    ">= k*noise within physical bounds. False means a term is "
                    "physically negligible and could not be excited without unphysical "
                    "values; the caller decides whether to keep this case.",
    )
    excitation_report: str = Field(
        "",
        description="Summary of excitation_check: each term's multiple of noise, and "
                    "the new term's peak multiple + where in the region it is strongest.",
    )

    # ---- traceability: how this plan differs from what evolve claimed ----
    role_corrections: list[str] = Field(
        default_factory=list,
        description="Each correction vs the evolve record's O/V/S/P tags, e.g. "
                    "'b: P->P (ok)', 'tau: was P, is actually integration var'.",
    )
    rationale: str = ""


def _ode_contract(record: dict) -> dict[str, Any] | None:
    """Extract the already-validated ODE structure from a typed pipeline record."""
    if record.get("model_family") != "ode":
        return None
    ode = record.get("ode_system")
    if not isinstance(ode, dict):
        raise SpecAgentError("typed ODE record is missing ode_system", trace=[])
    time_symbol = ode.get("time_symbol")
    target_state = ode.get("target_state")
    states = ode.get("states")
    if not isinstance(time_symbol, str) or not isinstance(target_state, str):
        raise SpecAgentError("ode_system needs time_symbol and target_state", trace=[])
    if not isinstance(states, list) or not states:
        raise SpecAgentError("ode_system needs a non-empty states list", trace=[])

    state_variables: list[str] = []
    state_rhs: list[str] = []
    initial_conditions: dict[str, float] = {}
    for state in states:
        if not isinstance(state, dict):
            raise SpecAgentError("ode_system.states must contain objects", trace=[])
        symbol = state.get("symbol")
        rhs = state.get("rhs")
        initial = state.get("initial_condition")
        if not isinstance(symbol, str) or not isinstance(rhs, str):
            raise SpecAgentError("each ODE state needs symbol and rhs", trace=[])
        if not isinstance(initial, (int, float)) or not math.isfinite(initial):
            raise SpecAgentError("each ODE state needs a finite initial_condition", trace=[])
        state_variables.append(symbol)
        state_rhs.append(rhs)
        initial_conditions[symbol] = float(initial)
    if len(set(state_variables)) != len(state_variables):
        raise SpecAgentError("ode_system state symbols must be distinct", trace=[])
    if target_state not in initial_conditions:
        raise SpecAgentError("ode_system target_state is not in states", trace=[])
    symbols = record.get("symbols", []) or []
    properties = record.get("symbol_properties", []) or []
    if len(symbols) != len(properties):
        raise SpecAgentError("ODE record symbols and roles have different lengths", trace=[])
    parameter_symbols = [
        symbol for symbol, role in zip(symbols, properties) if role == "P"
    ]
    return {
        "time_symbol": time_symbol,
        "target_state": target_state,
        "state_variables": state_variables,
        "state_rhs": state_rhs,
        "initial_conditions": initial_conditions,
        "parameter_symbols": parameter_symbols,
    }


def _validate_inherited_ode_spec(spec: DataGenSpec, contract: dict[str, Any]) -> None:
    """Ensure Stage 6 preserves the ODE system verified by Stage 3/evolution."""
    expected_states = contract["state_variables"]
    expected_rhs = contract["state_rhs"]
    expected_initial = contract["initial_conditions"]
    expected_time = contract["time_symbol"]
    expected_target = contract["target_state"]
    expected_parameters = contract["parameter_symbols"]

    if spec.equation_type != "ode_system" or spec.integrator != "integrate_system":
        raise ValueError(
            "inherited ODE records must use equation_type='ode_system' and "
            "integrator='integrate_system'"
        )
    if spec.dependent_variable != expected_target:
        raise ValueError(
            "ODE dependent_variable must be inherited target_state "
            f"'{expected_target}', got '{spec.dependent_variable}'"
        )
    if spec.state_variables != expected_states:
        raise ValueError(
            "ODE state_variables must preserve the inherited order: "
            f"expected {expected_states}, got {spec.state_variables}"
        )
    if spec.state_rhs != expected_rhs:
        raise ValueError("ODE state_rhs must exactly preserve the inherited ode_system")
    if spec.initial_conditions != expected_initial:
        raise ValueError(
            "ODE initial_conditions must exactly preserve the inherited ode_system"
        )
    parameter_symbols = [item.symbol for item in spec.parameters]
    if parameter_symbols != expected_parameters:
        raise ValueError(
            "ODE parameters must assign every inherited P symbol in order: "
            f"expected {expected_parameters}, got {parameter_symbols}"
        )
    time_axes = [item.symbol for item in spec.independent_variables]
    if time_axes != [expected_time]:
        raise ValueError(
            "ODE independent_variables must contain only inherited time axis "
            f"'{expected_time}', got {time_axes}"
        )
    target_index = expected_states.index(expected_target)
    if spec.rhs_for_integrator != expected_rhs[target_index]:
        raise ValueError("ODE rhs_for_integrator must equal the inherited target-state RHS")


def _attach_ode_benchmark_metadata(spec: dict, record: dict) -> dict:
    """Expose the upstream derivative target without changing integration semantics."""
    contract = _ode_contract(record)
    if contract is None:
        return spec
    target_symbol = record.get("target_symbol")
    if not isinstance(target_symbol, str) or not target_symbol:
        raise SpecAgentError("ODE record is missing target_symbol", trace=[])
    spec["benchmark_output"] = target_symbol
    spec["benchmark_target_state"] = contract["target_state"]
    # All integrated states are emitted as measured covariates for the RHS.
    spec["observed_variables"] = [contract["time_symbol"], *contract["state_variables"]]
    return spec


def attach_ode_benchmark_metadata(spec: dict, record: dict) -> dict:
    """Public migration hook for existing Specs and their source ODE records."""
    return _attach_ode_benchmark_metadata(spec, record)


def _validate_emitted_spec(
    spec: DataGenSpec,
    ode_contract: dict[str, Any] | None = None,
) -> None:
    """Reject malformed or incompatible plans before the data stage sees them."""
    try:
        expression = _sympify(spec.rhs_for_integrator)
    except Exception as exc:
        raise ValueError(f"rhs_for_integrator is not valid SymPy syntax: {exc}") from exc

    if spec.integrator == "integrate_basset":
        import sympy
        if not expression.atoms(sympy.Integral):
            raise ValueError(
                "integrate_basset requires an explicit Basset Integral; a delay term "
                "such as y(t - tau) must use integrate_dde or be unsupported"
            )
    if spec.integrator == "integrate_dde":
        from sympy.core.function import AppliedUndef
        target = spec.dependent_variable
        calls = list(expression.atoms(AppliedUndef))
        foreign = sorted(str(call) for call in calls if call.func.__name__ != target)
        if foreign:
            raise ValueError(
                "integrate_dde only supports one governed state; missing equations for "
                + ", ".join(foreign)
            )
        target_calls = [call for call in calls if call.func.__name__ == target]
        if not target_calls:
            raise ValueError(
                f"integrate_dde requires state calls such as {target}(t - tau)"
            )

    if ode_contract is not None:
        _validate_inherited_ode_spec(spec, ode_contract)


# ============================================================
# sympy helpers (deterministic) — the agent's "microscope".
# These are plain functions; the @tool wrappers below call them.
# ============================================================

def _sympify(expression: str):
    """Parse a pipeline expression into a sympy object. Raises on real failure.

    Pipeline symbols routinely collide with sympy's reserved singletons — `S`
    (SingletonRegistry), `I` (imaginary unit), `E`, `N`, `O`, `Q` — which makes a
    naive sympify blow up (e.g. `Vmax * S` -> Symbol * SingletonRegistry). To stay
    faithful to the equation's intent, every bare identifier is forced to a plain
    Symbol via a local namespace, EXCEPT names that are genuinely math functions
    (sin, exp, Derivative, Integral, ...), which we leave for sympy to resolve.
    """
    import re
    import sympy

    # Only names that are UNAMBIGUOUSLY math functions stay reserved for sympy.
    # Names like `gamma`, `beta`, `erf`, `pi` are deliberately NOT reserved: in
    # these physics/biology equations they are almost always parameter symbols,
    # and treating `gamma` as the Gamma function breaks parsing
    # (FunctionClass * Pow). If a real special function is ever needed, the agent
    # can note it; defaulting ambiguous names to Symbols is the safer choice here.
    reserved_funcs = {
        "Abs", "Max", "Min", "Piecewise", "Heaviside", "Derivative", "Integral",
        "sin", "cos", "tan", "asin", "acos", "atan", "atan2", "sinh", "cosh",
        "tanh", "asinh", "acosh", "atanh", "exp", "log", "ln", "sqrt", "sign",
        "floor", "ceiling", "pi",
    }
    names = set(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", expression))
    called = set(re.findall(r"\b([A-Za-z_][A-Za-z_0-9]*)\s*\(", expression))
    local_dict = {n: sympy.Symbol(n) for n in names
                  if n not in reserved_funcs and n not in called}
    local_dict.update({n: sympy.Function(n) for n in called if n not in reserved_funcs})

    try:
        return sympy.sympify(expression, locals=local_dict, evaluate=False)
    except Exception:
        return sympy.sympify(expression, locals=local_dict)


def _solve_with_timeout(eq, target, seconds: int = 8):
    """sympy.solve with a hard wall-clock cap (SIGALRM on Unix).

    sympy.solve can spin for tens of seconds on large transcendental expressions;
    left unguarded inside an agent tool it stalls the whole SDK run. We only need
    a yes/no on closed-form solvability, so a timeout that returns "no" is fine.
    """
    import signal
    import sympy

    def _handler(signum, frame):
        raise TimeoutError("solve timed out")

    old = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        return sympy.solve(eq, target, dict=False)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def _analyze_expression(expression: str, target_symbol: str) -> dict:
    """HARD structural facts about the expression. No interpretation, just sympy."""
    import sympy
    from sympy.core.function import AppliedUndef, Derivative
    from sympy import Integral

    try:
        expr = _sympify(expression)
    except Exception as e:
        return {"ok": False, "error": f"sympify failed: {type(e).__name__}: {e}"}

    free_symbols = sorted({str(s) for s in expr.free_symbols})

    applied = expr.atoms(AppliedUndef)
    functions_of: dict[str, list[str]] = {}
    for f in applied:
        fname = f.func.__name__
        fargs = sorted({str(a) for a in f.args})
        functions_of.setdefault(fname, sorted(set(fargs)))

    target_calls = [call for call in applied if call.func.__name__ == target_symbol]
    delayed_target_calls = []
    time_symbol = sympy.Symbol("t")
    for call in target_calls:
        if len(call.args) != 1:
            continue
        try:
            offset = sympy.simplify(time_symbol - call.args[0])
        except Exception:
            continue
        if offset != 0:
            delayed_target_calls.append(str(call))
    ungoverned_functions = sorted(
        str(call) for call in applied if call.func.__name__ != target_symbol
    )

    derivs = expr.atoms(Derivative)
    derivative_info = []
    max_order = 0
    for d in derivs:
        try:
            fn = d.expr.func.__name__ if hasattr(d.expr, "func") else str(d.expr)
        except Exception:
            fn = str(d.expr)
        order = sum(int(n) for _, n in d.variable_count)
        wrt = sorted({str(v) for v, _ in d.variable_count})
        max_order = max(max_order, order)
        derivative_info.append({"of": fn, "order": order, "wrt": wrt})

    integrals = expr.atoms(Integral)
    integral_info = []
    for it in integrals:
        try:
            dummies = sorted({str(v[0]) for v in it.limits})
        except Exception:
            dummies = []
        integral_info.append({"integration_vars": dummies, "snippet": str(it)[:120]})

    explicit_solution = None
    solvable = False
    target_in_expr = sympy.Symbol(target_symbol) in expr.free_symbols
    if not derivs and not integrals and not target_calls:
        if not target_in_expr:
            # Expression is already y = f(...) — the target does not appear on the
            # RHS, so it is trivially explicit. No need to call solve() (which can
            # hang for tens of seconds on large transcendental expressions).
            solvable = True
            explicit_solution = [str(expr)[:120]]
        else:
            # Target appears inside the expression: genuinely implicit. Try to
            # solve, but guard with a hard timeout so a pathological expression
            # cannot stall the agent (the failure mode that crashed the SDK run).
            try:
                sols = _solve_with_timeout(sympy.Eq(expr, 0),
                                           sympy.Symbol(target_symbol), seconds=8)
                if sols:
                    solvable = True
                    explicit_solution = [str(s) for s in sols][:3]
            except Exception:
                solvable = False

    if integral_info:
        hint = "integro_diff"
    elif delayed_target_calls:
        hint = "delay_differential"
    elif target_calls:
        hint = "ode1_or_system"
    elif max_order >= 2 or len(functions_of) >= 2:
        hint = "ode_higher_or_system"
    elif max_order == 1:
        hint = "ode1"
    elif solvable:
        hint = "explicit"
    else:
        hint = "implicit_or_explicit"

    return {
        "ok": True,
        "free_symbols": free_symbols,
        "functions_of": functions_of,
        "target_function_calls": sorted(str(call) for call in target_calls),
        "delayed_target_calls": sorted(delayed_target_calls),
        "ungoverned_functions": ungoverned_functions,
        "derivatives": derivative_info,
        "max_derivative_order": max_order,
        "integral_kernels": integral_info,
        "explicitly_solvable_for_target": solvable,
        "explicit_solution_preview": explicit_solution,
        "classification_hint": hint,
        "note": "Roles/type are YOURS to decide; this is structural fact + a hint.",
    }


def _check_substitution(expression: str, assignments: dict, target_symbol: str) -> dict:
    """Substitute numeric values and report finite/real/complex/NaN at a test point."""
    import math
    import sympy

    try:
        expr = _sympify(expression)
    except Exception as e:
        return {"ok": False, "error": f"sympify failed: {type(e).__name__}: {e}"}

    subs = {}
    for name, val in (assignments or {}).items():
        try:
            subs[sympy.Symbol(name)] = float(val)
        except (TypeError, ValueError):
            return {"ok": False, "error": f"non-numeric assignment for '{name}': {val!r}"}

    try:
        substituted = expr.subs(subs)
        from sympy.core.function import AppliedUndef
        for f in list(substituted.atoms(AppliedUndef)):
            fname = f.func.__name__
            if fname in (assignments or {}):
                substituted = substituted.subs(f, float(assignments[fname]))
        value = complex(sympy.N(substituted))
    except Exception as e:
        resid = expr.subs(subs)
        return {"ok": False, "error": f"evaluation failed: {type(e).__name__}: {e}",
                "residual_free_symbols": sorted({str(s) for s in resid.free_symbols})}

    re, im = value.real, value.imag
    is_finite = math.isfinite(re) and math.isfinite(im)
    is_real = abs(im) < 1e-9 * (1 + abs(re))
    verdict = "ok" if (is_finite and is_real) else (
        "complex" if (is_finite and not is_real) else "non_finite")
    return {
        "ok": True,
        "value_real": re,
        "value_imag": im,
        "is_finite": is_finite,
        "is_real": is_real,
        "verdict": verdict,
        "residual_free_symbols": sorted({str(s) for s in
                                         (substituted.free_symbols
                                          if hasattr(substituted, "free_symbols") else set())}),
    }


# ============================================================
# Excitation check — does every term leave a visible mark in the data?
# ============================================================
#
# The rule (k=5 by default): each additive term, and in particular the NEW term
# this evolution step introduced (the difference between the equation E and its
# parent), must move the dependent variable by at least k * sigma somewhere in the
# sampling region — otherwise it is drowned by the noise and is effectively absent
# from the data. We compute this FORWARD (no re-fitting): substitute the chosen
# parameter values, evaluate on the chosen grid, and measure each term's effect
# against the noise floor sigma. For ODEs the effect is measured on the SOLUTION
# trajectory (solve child system vs parent system), because a term's size in an RHS
# is not the same as its effect on the observed data.

_MAX_STATIC_EXCITATION_SAMPLES = 4096


def _representative_static_samples(indep: list[dict]) -> tuple[list[str], dict[str, object]]:
    """Return a bounded, deterministic design instead of a Cartesian grid."""
    import numpy as np

    axis_names = [str(iv["symbol"]) for iv in indep]
    requested = max(int(iv.get("n_points", 200)) for iv in indep)
    n_samples = min(_MAX_STATIC_EXCITATION_SAMPLES, max(512, requested))
    dimension = len(axis_names)

    try:
        from scipy.stats import qmc

        # Sobol requires a power of two for balance; truncate to the requested cap.
        power = math.ceil(math.log2(n_samples))
        unit = qmc.Sobol(d=dimension, scramble=True, seed=0).random_base2(power)
        unit = unit[:n_samples]
        method = "sobol"
    except Exception:
        # Keep the check available in minimal SciPy installations as well.
        unit = np.random.default_rng(0).random((n_samples, dimension))
        method = "uniform_fallback"

    samples: dict[str, object] = {}
    for column, iv in enumerate(indep):
        lo, hi = (float(iv["range"][0]), float(iv["range"][1]))
        values = unit[:, column]
        if iv.get("scale") == "log":
            if lo <= 0 or hi <= 0:
                raise ValueError(f"log-scale excitation range must be positive for '{iv['symbol']}'")
            samples[axis_names[column]] = 10 ** (
                math.log10(lo) + values * (math.log10(hi) - math.log10(lo))
            )
        else:
            samples[axis_names[column]] = lo + values * (hi - lo)
    return axis_names, {
        "samples": samples,
        "method": method,
        "n_samples": n_samples,
    }


def _integrate_ode_contract(
    contract: dict[str, Any],
    assignments: dict,
    tgrid,
):
    """Integrate one closed ODE contract on a prescribed common time grid."""
    import numpy as np
    import sympy
    from scipy.integrate import solve_ivp

    states = list(contract["state_variables"])
    rhs_list = list(contract["state_rhs"])
    time_symbol = str(contract["time_symbol"])
    parameter_symbols = list(contract["parameter_symbols"])
    initial_conditions = dict(contract["initial_conditions"])
    if not states or len(states) != len(rhs_list):
        raise ValueError("ODE contract needs aligned non-empty states and RHS expressions")

    try:
        parameter_values = [float(assignments[name]) for name in parameter_symbols]
    except KeyError as exc:
        raise ValueError(f"missing numeric assignment for ODE parameter '{exc.args[0]}'") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError("ODE parameter assignments must be numeric") from exc
    if not all(math.isfinite(value) for value in parameter_values):
        raise ValueError("ODE parameter assignments must be finite")

    param_subs = {
        sympy.Symbol(name): value
        for name, value in zip(parameter_symbols, parameter_values)
    }
    allowed = set(states) | {time_symbol} | set(parameter_symbols)
    arguments = [sympy.Symbol(time_symbol)] + [sympy.Symbol(name) for name in states]
    compiled = []
    for state, rhs in zip(states, rhs_list):
        parsed = _sympify(rhs)
        unknown = sorted(str(symbol) for symbol in parsed.free_symbols if str(symbol) not in allowed)
        if unknown:
            raise ValueError(
                f"ODE RHS for '{state}' uses undeclared symbols: {', '.join(unknown)}"
            )
        compiled.append(sympy.lambdify(arguments, parsed.subs(param_subs), modules="numpy"))

    try:
        y0 = [float(initial_conditions[state]) for state in states]
    except KeyError as exc:
        raise ValueError(f"ODE contract lacks an initial condition for '{exc.args[0]}'") from exc
    if not all(math.isfinite(value) for value in y0):
        raise ValueError("ODE initial conditions must be finite")

    def system(time, values):
        return [float(func(time, *values)) for func in compiled]

    solution = solve_ivp(
        system,
        (float(tgrid[0]), float(tgrid[-1])),
        y0,
        t_eval=tgrid,
        method="RK45",
        rtol=1e-7,
        atol=1e-9,
    )
    if not solution.success:
        raise ValueError(f"integration failed: {solution.message}")
    if solution.t.shape != tgrid.shape or solution.y.shape != (len(states), len(tgrid)):
        raise ValueError("integration did not return the complete requested time grid")
    if not np.isfinite(solution.y).all():
        raise ValueError("integration produced non-finite state values")
    return solution

def _excitation_check(
    expression: str,
    parent_expression: str | None,
    target_symbol: str,
    assignments: dict,
    indep: list[dict],
    sigma: float,
    is_ode: bool,
    k: float = 5.0,
    ode_contract: dict[str, Any] | None = None,
    parent_ode_contract: dict[str, Any] | None = None,
) -> dict:
    """Forward-evaluate term balance and new-term excitation against k*sigma.

    assignments : every parameter -> value (independent vars are swept, not fixed).
    indep       : [{"symbol","range":[lo,hi],"n_points"}], the sampling region.
    sigma       : intended absolute noise std on the dependent variable.
    is_ode      : if True, measure effects on the integrated solution, not the RHS.
    Returns a verdict dict the agent can act on (which term is too weak, where the
    new term is strongest, and the multiple of sigma it reaches).
    """
    import numpy as np
    import sympy

    if sigma is None or sigma <= 0:
        return {"ok": False, "error": "sigma must be > 0 to judge visibility against noise"}
    if not indep:
        return {"ok": False, "error": "need at least one independent variable to sample"}

    try:
        expr = _sympify(expression)
    except Exception as e:
        return {"ok": False, "error": f"sympify(E) failed: {type(e).__name__}: {e}"}

    axis_names = [str(iv["symbol"]) for iv in indep]

    param_subs = {}
    for nm, val in (assignments or {}).items():
        # The dependent variable is a state, not a fixed constant — never substitute
        # it into the expression (its value comes from the grid / the integration).
        if nm == target_symbol:
            continue
        try:
            param_subs[sympy.Symbol(nm)] = float(val)
        except (TypeError, ValueError):
            return {"ok": False, "error": f"non-numeric assignment for '{nm}': {val!r}"}

    def _lam(e):
        syms = [sympy.Symbol(a) for a in axis_names]
        return sympy.lambdify(syms, e.subs(param_subs), modules="numpy")

    # ---- ODE path: compare integrated child and parent trajectories ----
    if is_ode:
        if not parent_expression:
            return {"ok": True, "mode": "ode", "note": "no parent given; cannot isolate "
                    "the new term on the trajectory. Term-balance skipped.",
                    "new_term_sigma_multiple": None, "passes": None}
        if len(axis_names) != 1:
            return {"ok": False, "error": "ODE excitation needs exactly one indep (time)"}
        tname = axis_names[0]
        lo, hi = (float(indep[0]["range"][0]), float(indep[0]["range"][1]))
        n_time = min(max(int(indep[0].get("n_points", 200)), 64), 4000)
        tgrid = np.linspace(lo, hi, n_time)

        # Typed ODE records carry every state RHS and initial condition. Compare
        # whole systems so a mechanism added to a non-target state is still visible
        # through its downstream effect on the observed target state.
        if ode_contract is not None or parent_ode_contract is not None:
            if ode_contract is None or parent_ode_contract is None:
                return {
                    "ok": False,
                    "error": "typed ODE excitation needs both child and parent ode_system contracts",
                }
            try:
                target_state = str(ode_contract["target_state"])
                parent_target = str(parent_ode_contract["target_state"])
                if target_state != parent_target:
                    raise ValueError(
                        f"child target_state '{target_state}' differs from parent '{parent_target}'"
                    )
                child_solution = _integrate_ode_contract(ode_contract, assignments, tgrid)
                parent_solution = _integrate_ode_contract(parent_ode_contract, assignments, tgrid)
                child_index = list(ode_contract["state_variables"]).index(target_state)
                parent_index = list(parent_ode_contract["state_variables"]).index(target_state)
                diff = np.abs(child_solution.y[child_index] - parent_solution.y[parent_index])
                max_diff = float(np.max(diff))
                at = float(tgrid[int(np.argmax(diff))])
                mult = max_diff / sigma
                return {
                    "ok": True,
                    "mode": "ode_system",
                    "comparison": "full_child_parent_systems",
                    "target_state": target_state,
                    "child_state_count": len(ode_contract["state_variables"]),
                    "parent_state_count": len(parent_ode_contract["state_variables"]),
                    "n_time_points": n_time,
                    "new_term_max_effect": max_diff,
                    "new_term_sigma_multiple": mult,
                    "strongest_at": {tname: at},
                    "k": k,
                    "passes": bool(mult >= k),
                    "advice": (
                        "new mechanism is visible on the target trajectory"
                        if mult >= k else
                        f"new mechanism peaks at only {mult:.2f}*sigma (need {k}); extend "
                        f"the {tname} range or adjust physically valid coefficients"
                    ),
                }
            except Exception as exc:
                return {
                    "ok": False,
                    "error": f"ODE-system excitation failed: {type(exc).__name__}: {exc}",
                }

        # Legacy scalar ODE records have no closed-system metadata. Retain the
        # former comparison so old files are still usable, but typed records take
        # the full-system path above.
        from scipy.integrate import solve_ivp
        tsym, ysym = sympy.Symbol(tname), sympy.Symbol(target_symbol)

        def _rhs_fn(e):
            f = sympy.lambdify([tsym, ysym], e.subs(param_subs), modules="numpy")
            return lambda tt, yy: float(f(tt, yy[0]))

        try:
            par = _sympify(parent_expression)
            fE, fP = _rhs_fn(expr), _rhs_fn(par)
            y0 = [float((assignments or {}).get(target_symbol, 0.0))]
            span = (float(tgrid[0]), float(tgrid[-1]))
            solE = solve_ivp(fE, span, y0, t_eval=tgrid, method="RK45", rtol=1e-7, atol=1e-9)
            solP = solve_ivp(fP, span, y0, t_eval=tgrid, method="RK45", rtol=1e-7, atol=1e-9)
            if not (solE.success and solP.success):
                return {"ok": False, "error": f"integration failed (E:{solE.success}, P:{solP.success})"}
            diff = np.abs(solE.y[0] - solP.y[0])
            max_diff = float(np.nanmax(diff))
            at = float(tgrid[int(np.nanargmax(diff))])
            mult = max_diff / sigma
            return {
                "ok": True, "mode": "ode",
                "new_term_max_effect": max_diff,
                "new_term_sigma_multiple": mult,
                "strongest_at": {tname: at},
                "k": k, "passes": bool(mult >= k),
                "advice": ("new term is visible" if mult >= k else
                           f"new term peaks at only {mult:.2f}*sigma (need {k}); extend the "
                           f"{tname} range toward where E and parent diverge, or increase the "
                           f"new term's coefficient (within physical bounds)"),
            }
        except Exception as e:
            return {"ok": False, "error": f"ode excitation failed: {type(e).__name__}: {e}"}

    # ---- static path: additive term balance + new-term effect ----
    try:
        axis_names, design = _representative_static_samples(indep)
        grid = design["samples"]
        terms = expr.as_ordered_terms() if expr.is_Add else [expr]
        term_report = []
        total_rms = 0.0
        for ti in terms:
            try:
                vals = np.abs(np.asarray(_lam(ti)(*[grid[a] for a in axis_names]),
                                         dtype=float))
                rms = float(np.sqrt(np.nanmean(vals ** 2)))
            except Exception:
                rms = float("nan")
            term_report.append({"term": str(ti)[:80], "rms": rms,
                                 "sigma_multiple": (rms / sigma) if rms == rms else None})
            if rms == rms:
                total_rms = max(total_rms, rms)

        # New-term effect = | E - parent | on the grid. Do not symbolically simplify
        # this difference: evolved expressions can make SymPy expand indefinitely.
        new_term = None
        if parent_expression:
            try:
                par = _sympify(parent_expression)
                current_values = np.asarray(
                    _lam(expr)(*[grid[a] for a in axis_names]), dtype=float,
                )
                parent_values = np.asarray(
                    _lam(par)(*[grid[a] for a in axis_names]), dtype=float,
                )
                dv = np.abs(current_values - parent_values)
                max_eff = float(np.nanmax(dv))
                idx = int(np.nanargmax(dv))
                mult = max_eff / sigma
                new_term = {
                    "delta_expr": "evaluated numerically as current expression minus parent",
                    "max_effect": max_eff,
                    "sigma_multiple": mult,
                    "strongest_at": {a: float(grid[a][idx]) for a in axis_names},
                    "passes": bool(mult >= k),
                }
            except Exception as e:
                new_term = {"error": f"could not form E-parent: {type(e).__name__}: {e}"}

        weak = [t for t in term_report
                if t["sigma_multiple"] is not None and t["sigma_multiple"] < k]
        return {
            "ok": True, "mode": "explicit",
            "k": k, "sigma": sigma,
            "sampling": {
                "method": design["method"],
                "n_samples": design["n_samples"],
                "n_dimensions": len(axis_names),
            },
            "terms": term_report,
            "weak_terms": weak,
            "new_term": new_term,
            "advice": ("all terms visible" if not weak and (new_term or {}).get("passes", True)
                       else "some terms (or the new term) fall below k*sigma; rescale their "
                            "coefficients toward the dominant term, or move the sampling region "
                            "to where they are strongest — staying within physical bounds"),
        }
    except Exception as e:
        return {"ok": False, "error": f"explicit excitation failed: {type(e).__name__}: {e}"}


def _auto_balance(
    expression: str,
    parent_expression: str | None,
    target_symbol: str,
    assignments: dict,
    indep: list[dict],
    sigma: float,
    is_ode: bool,
    k: float = 5.0,
    bound: float = 1e6,
    max_iter: int = 8,
    ode_contract: dict[str, Any] | None = None,
    parent_ode_contract: dict[str, Any] | None = None,
) -> dict:
    """Numerically solve coefficients so every additive term — and the NEW term —
    reaches at least k*sigma, instead of leaving the agent to hand-tune them.

    Strategy (cheap, no LLM): an additive term is almost always *linear in its own
    leading coefficient*, so to lift a term from m*sigma to k*sigma we multiply that
    coefficient by (k/m). We:
      1. map each additive term to the single parameter that scales it (a parameter
         that appears in that term and in no other term);
      2. run _excitation_check, find weak terms, and rescale each one's coefficient
         by (target/current) with a safety margin;
      3. iterate (terms couple through `total`, and the new-term effect depends on
         the parent), stopping when nothing is weak or coefficients hit `bound`.

    Returns {"ok", "assignments" (tuned), "report" (final excitation verdict),
    "changed" (param->(old,new)), "converged", "note"}.
    Parameters it cannot move within `bound` are reported, not forced.
    """
    import sympy

    try:
        expr = _sympify(expression)
    except Exception as e:
        return {"ok": False, "error": f"sympify(E) failed: {type(e).__name__}: {e}"}

    terms = expr.as_ordered_terms() if expr.is_Add else [expr]

    # For each term, identify its OUTERMOST linear coefficient: a parameter that is
    # a top-level multiplicative factor (so the term scales linearly with it). This
    # deliberately EXCLUDES parameters buried inside tanh/exp/Max/powers (e.g. `mu`
    # in tanh(mu*x)), where scaling would saturate rather than amplify. Several terms
    # may legitimately share one coefficient (e.g. +beta*... and -beta*...).
    indep_names = {iv["symbol"] for iv in indep}
    reserved = indep_names | {target_symbol}
    term_coeff: list[str | None] = []
    for ti in terms:
        top_syms = [str(f) for f in sympy.Mul.make_args(ti)
                    if f.is_Symbol and str(f) not in reserved]
        term_coeff.append(top_syms[0] if top_syms else None)

    cur = dict(assignments or {})
    changed: dict[str, tuple] = {}

    def _run():
        return _excitation_check(expression, parent_expression, target_symbol,
                                 cur, indep, sigma, is_ode, k,
                                 ode_contract=ode_contract,
                                 parent_ode_contract=parent_ode_contract)

    rep = _run()
    if not rep.get("ok"):
        return {"ok": False, "error": rep.get("error", "excitation_check failed"),
                "assignments": cur}

    # ODE mode: only the new-term multiple is meaningful; scale the new term's coeff.
    if is_ode:
        # best-effort: bump any single parameter unique to (E - parent)
        return {"ok": True, "assignments": cur, "report": rep,
                "changed": {}, "converged": rep.get("passes") is True,
                "note": "ODE auto-balance is limited to reporting; tune the new "
                        "term coefficient guided by new_term_sigma_multiple."}

    converged = False
    for _ in range(max_iter):
        weak = list(rep.get("weak_terms", []))
        nt = rep.get("new_term") or {}
        nt_weak = nt.get("sigma_multiple") is not None and not nt.get("passes", True)
        if not weak and not nt_weak:
            converged = True
            break

        moved_any = False
        # rescale each weak additive term via its private coefficient
        for w in weak:
            tstr = w["term"]
            mult = w.get("sigma_multiple") or 0.0
            # find which term this report row corresponds to
            idx = next((i for i, ti in enumerate(terms) if str(ti)[:80] == tstr), None)
            if idx is None:
                continue
            coeff = term_coeff[idx]
            if coeff is None or coeff not in cur:
                continue  # no top-level linear coefficient; can't scale this term
            if mult <= 0:
                factor = 10.0  # term is ~0 here; try a decade then re-measure
            else:
                factor = (k / mult) * 1.3  # 30% margin above threshold
            old = float(cur[coeff])
            new = old * factor if old != 0 else (k * sigma)
            if abs(new) > bound:
                new = bound if new > 0 else -bound
            if new != old:
                cur[coeff] = new
                changed[coeff] = (old, new)
                moved_any = True

        if not moved_any:
            break
        rep = _run()
        if not rep.get("ok"):
            break

    return {"ok": True, "assignments": cur, "report": rep, "changed": changed,
            "converged": converged,
            "note": ("all terms reach k*sigma" if converged else
                     "some terms still weak — they may lack a private coefficient, "
                     "be coupled, or need a range change / be genuinely negligible")}


# ============================================================
# Prompts (unchanged contract; the SDK delivers them differently)
# ============================================================

SYSTEM_PROMPT = """\
You are a scientific-computing expert preparing a symbolic-regression dataset.
You are given ONE governing equation produced by an equation-evolution pipeline,
together with the role labels it assigned (which symbol is the output, which are
independent variables, which are parameters) and any range/magnitude hints.

Treat those labels as a PRIOR, not as truth: the upstream stage proposes, you
verify. The expression (the math) is trustworthy; the labels are usually right
but sometimes wrong, especially the roles and the implied equation TYPE. Your job
is to CONFIRM-OR-CORRECT them against the structure of the expression and produce
a plan for generating data points. You do NOT compute any data — only the plan.

You have sympy tools. They are your source of structural truth — USE THEM rather
than judging from intuition or from the labels alone:
  1. ALWAYS call analyze_expression first. Compare its facts (derivatives, integral
     kernels, applied functions, target-in-expression, solvability) against the
     incoming labels.
       - Where the label AGREES with the structure, keep it (a quick confirmation).
       - Where it CONFLICTS, the structure WINS — override the label.
     Decide each role on this basis:
       - dependent variable  = the quantity the equation determines: the function
         under the highest derivative for an ODE, or the symbol on the LHS / solved
         for in an explicit/implicit relation.
       - independent variables = the axes the solution is a function of (e.g. t, x)
         — variables differentiated/integrated w.r.t., or the natural sampling axes.
         These get sampling RANGES.
       - parameters = every remaining free symbol; constants you FIX to a number.
       - integration dummy variables (e.g. tau inside an Integral) are NEITHER
         variables nor parameters — never sample or fix them.
  2. For ranges and parameter magnitudes, PREFER the provided hints when present
     and physically sensible; only depart from them when they are missing or would
     make the expression blow up. Then call check_substitution at a representative
     point to confirm the expression stays finite and real, and fix any choice that
     returns complex/non_finite.
  3. For higher-order ODEs or coupled systems, reduce to first order and fill
     state_variables + state_rhs (aligned, ordered) plus initial_conditions.
  4. Map the type to an integrator:
       explicit      -> evaluate_explicit
       implicit      -> root_solve_implicit
       ode1          -> integrate_ode
       ode_higher    -> integrate_system   (after reduction)
       ode_system    -> integrate_system
       delay_differential -> integrate_dde ONLY for scalar first-order, fixed-delay
                             y(t-tau) equations with no other ungoverned f(t).
       integro_diff  -> integrate_basset ONLY for an explicit standard Basset
                        Integral(Derivative(y(tau),tau)/sqrt(t-tau), (tau,0,t)).
       (if nothing fits: equation_type/integrator = "unsupported")
     A time-delay y(t-tau) is NOT a Basset integral. If a second dynamic state
     (for example h(t)) appears without its own governing equation, mark the plan
     unsupported. Never silently replace h(t) with a constant parameter.
  5. EXCITATION — make every term visible in the data. A term that is too small,
     or that only matters in a region you did not sample, leaves no mark once noise
     is added, so a far simpler ancestor equation could fit the data just as well.
     That destroys the benchmark. To prevent it:
       (a) Pick a noise level `sigma` (absolute std on the dependent variable) that
           is small vs the dominant term but is the yardstick for "visible".
       (b) For explicit/implicit equations, call auto_balance FIRST with a starting
           set of parameter values, the indep ranges, and sigma. It SOLVES the
           coefficients so every term reaches {K}*sigma and returns tuned
           `assignments` — adopt those values. (For ODE/system/integro_diff,
           auto_balance only reports; use excitation_check with is_ode=true instead.)
       (c) Call excitation_check to CONFIRM the (auto-balanced) values: every term,
           and the new term in particular, must reach at least {K}*sigma somewhere in
           the region. If auto_balance returned converged=false and some term is still
           weak, that term has no top-level linear coefficient (the symbol is inside
           tanh/exp/Max, or terms are coupled). Then either:
             - move / widen the sampling range to where excitation_check says that
               term is strongest (e.g. extend t into the regime where a drag term
               bites), or
             - if no PHYSICALLY reasonable coefficient or range makes it reach
               {K}*sigma, treat it as negligible for this phenomenon: say so in
               `rationale` and set `excitation_ok=false`.
           Stay within physically reasonable coefficients and ranges.
           IMPORTANT: do NOT loop forever rebalancing. With auto_balance you should
           usually need only ONE excitation_check to confirm. After at most ~3 rounds
           total, you MUST call emit_data_gen_spec with your best plan —
           set excitation_ok=false if some term is still weak. Emitting a flagged
           plan is REQUIRED; running out of turns without emitting is a failure.
       Put the sigma you settled on in the spec's `noise` field, and summarise the
       per-term multiples + the new term's multiple in `excitation_report`.
  6. In role_corrections, record BOTH confirmations and overrides versus the
     incoming labels (e.g. 't: V->V (confirmed)', 'm: V->P (overridden: fixed
     physical constant)'), so the line is a full audit of agree/disagree.

When done, call emit_data_gen_spec exactly once. Keep ranges and parameter values
in sensible physical magnitudes; prefer ~100-500 sample points unless the dynamics
demand more. After it succeeds, reply with one short confirming sentence.
"""

USER_TEMPLATE = """\
DISCIPLINE: {discipline}
PHENOMENON CONTEXT:
{scenario_text}

EQUATION (target = expression):
  {target_symbol} = {expression}

{ode_contract_block}

PARENT EQUATION (the previous generation — what this step evolved FROM; the NEW
term is the difference E - parent, and excitation_check measures its effect):
  {parent_block}

LABELS THE PIPELINE ATTACHED (a PRIOR — confirm against the structure, override
only where the math disagrees):
{labels_block}

SUGGESTED RANGES / MAGNITUDES FROM THE EVOLUTION STEP (prefer these when sensible):
{range_hints}

{sampling_replan_block}

For static records, confirm-or-correct roles and equation type. For a typed ODE
contract, do NOT re-derive, omit, reorder, or rewrite the state system: choose
only its time sampling range, fixed parameter values, noise, and expectations.
Then use excitation_check to ensure every term (especially the new one) is
visible above the noise, and emit the data-generation spec.
"""


def _labels_block(record: dict) -> str:
    syms = record.get("symbols", [])
    descs = record.get("symbol_descriptions", [])
    props = record.get("symbol_properties", [])
    rows = []
    role_name = {
        "O": "claimed-output/target derivative",
        "V": "claimed-input/time axis",
        "S": "claimed-dynamic state",
        "P": "claimed-parameter",
    }
    for i, s in enumerate(syms):
        role = props[i] if i < len(props) else "?"
        desc = descs[i] if i < len(descs) else ""
        rows.append(f"  {s} [{role_name.get(role, role)}] — {desc}")
    return "\n".join(rows) if rows else "  (no labels recorded)"


def _range_hints(record: dict) -> str:
    rng = record.get("new_symbol_range_suggestions", {}) or {}
    if not rng:
        return "  (none)"
    return "\n".join(f"  {k}: {v}" for k, v in rng.items())


def _sampling_replan_block(sampling_replan: dict | None) -> str:
    """Make a second Spec-Agent pass a strictly range-only experimental redesign."""
    if not sampling_replan:
        return "SAMPLING REPLAN: none; create the initial complete DataGenSpec."
    baseline = sampling_replan.get("baseline_spec", {})
    report = sampling_replan.get("parent_refit_report", {})
    axes = [
        {key: item.get(key) for key in ("symbol", "range", "n_points", "scale")}
        for item in baseline.get("independent_variables", []) or []
    ]
    locked = {
        key: baseline.get(key)
        for key in ("equation_type", "integrator", "dependent_variable", "parameters",
                    "rhs_for_integrator", "state_variables", "state_rhs",
                    "initial_conditions", "noise")
    }
    return (
        "SAMPLING REPLAN — THIS IS THE ONE ALLOWED REDESIGN PASS:\n"
        "The equation and its initial spec were valid, but a refitted parent still "
        f"achieved test R²={report.get('parent_to_child_r2')} (threshold "
        f"{report.get('threshold_r2')}). The goal is to make an existing structural "
        "difference observable in a physically plausible experiment.\n"
        f"DIAGNOSTIC FROM THE INITIAL GATE (where refitted-parent residual was largest):\n"
        f"{json.dumps(report.get('residual_hotspots', {}), ensure_ascii=False)}\n"
        "You MUST keep every locked field below exactly unchanged. You may change ONLY "
        "the numeric `range` of each existing independent variable. Do not add/remove "
        "variables; do not alter n_points, scale, parameters, noise, initial conditions, "
        "RHS, target, equation type, or ODE system. Select a physically reasonable, "
        "numerically stable range where the child-parent difference is observable. Call "
        "excitation_check again using the NEW range before emitting.\n"
        f"CURRENT AXES (only their range may change):\n{json.dumps(axes, ensure_ascii=False)}\n"
        f"LOCKED FIELDS:\n{json.dumps(locked, ensure_ascii=False)}\n"
    )


def validate_sampling_replan(baseline_spec: dict, replanned_spec: dict) -> None:
    """Enforce that the optional second Spec-Agent pass changed ranges only."""
    locked_fields = (
        "equation_type", "integrator", "dependent_variable", "parameters",
        "rhs_for_integrator", "state_variables", "state_rhs", "initial_conditions", "noise",
    )
    changed = [name for name in locked_fields if baseline_spec.get(name) != replanned_spec.get(name)]
    if changed:
        raise ValueError("sampling replan changed locked field(s): " + ", ".join(changed))
    before = baseline_spec.get("independent_variables", []) or []
    after = replanned_spec.get("independent_variables", []) or []
    if len(before) != len(after):
        raise ValueError("sampling replan changed the number of independent variables")
    any_range_changed = False
    for old, new in zip(before, after):
        if old.get("symbol") != new.get("symbol"):
            raise ValueError("sampling replan changed an independent-variable symbol")
        if old.get("n_points", 200) != new.get("n_points", 200):
            raise ValueError("sampling replan changed n_points")
        if old.get("scale", "linear") != new.get("scale", "linear"):
            raise ValueError("sampling replan changed sampling scale")
        new_range = new.get("range", [])
        if len(new_range) != 2 or not all(isinstance(v, (int, float)) and math.isfinite(v)
                                          for v in new_range) or new_range[0] >= new_range[1]:
            raise ValueError(f"sampling replan supplied an invalid range for {new.get('symbol')}")
        any_range_changed |= list(old.get("range", [])) != list(new_range)
    if not any_range_changed:
        raise ValueError("sampling replan did not change any independent-variable range")


def _ode_contract_block(contract: dict[str, Any] | None) -> str:
    """Explain the ODE inheritance boundary to both supported agent providers."""
    if contract is None:
        return "ODE SYSTEM CONTRACT: none; infer the structure from the static expression."
    return (
        "ODE SYSTEM CONTRACT (already structurally validated upstream):\n"
        + json.dumps(contract, ensure_ascii=False, indent=2)
        + "\nREQUIRED DATA SPEC MAPPING:\n"
        + "- equation_type = 'ode_system'; integrator = 'integrate_system';\n"
        + "- dependent_variable = target_state;\n"
        + "- independent_variables = the one time_symbol only;\n"
        + "- state_variables, state_rhs, initial_conditions, and rhs_for_integrator "
          "must exactly inherit this contract.\n"
        + "- parameters must assign every listed parameter_symbols exactly once; values "
          "remain your data-design choice.\n"
    )


# ============================================================
# The agentic run for ONE record, on the official SDK.
# ============================================================

class SpecAgentError(RuntimeError):
    """Carry the tool/QA trace when the agent fails to produce a spec."""
    def __init__(self, message: str, trace: list[dict]):
        super().__init__(message)
        self.trace = trace


async def plan_data_generation_async(
    record: dict,
    discipline: str,
    model: str = "claude-opus-4-7",
    max_turns: int = 18,
    cli_path: str | None = None,
    verbose: bool = True,
    parent: dict | None = None,
    sampling_replan: dict | None = None,
    k_sigma: float = 5.0,
    max_budget_usd: float | None = 2.5,
) -> dict:
    """Run the SDK tool-augmented agent and return a validated DataGenSpec dict.

    `parent` is the previous-generation record (same scenario lineage). When given,
    the agent can call excitation_check to confirm the NEW term this step added
    moves the data by at least `k_sigma` * noise somewhere in the sampling region.

    The returned dict is the validated spec plus a `_trace` field recording every
    tool call (like novelty_check's qa_history). Raises SpecAgentError on failure.
    """
    if _SDK_IMPORT_ERROR is not None:
        raise SpecAgentError(
            "Missing claude_agent_sdk. Install it in this Python environment "
            "and ensure the claude CLI is available.",
            trace=[],
        )

    target_symbol = record.get("target_symbol", "y")
    expression = record.get("expression", "")
    if not expression:
        raise SpecAgentError("record has no 'expression'", trace=[])
    ode_contract = _ode_contract(record)
    parent_expression = (parent or {}).get("expression")
    parent_ode_contract = _ode_contract(parent) if parent is not None else None
    if sampling_replan:
        baseline = sampling_replan.get("baseline_spec") or {}
        if not baseline:
            raise SpecAgentError("sampling_replan requires baseline_spec", trace=[])

    # Per-run state captured by the in-process tools (closures).
    trace: list[dict] = []
    captured: dict = {"spec": None, "excitation_ran": False, "emit_rejected": False}

    # ---- define the three tools as in-process MCP tools ----

    @tool(
        "analyze_expression",
        "Parse a sympy expression and return HARD structural facts: free symbols, "
        "applied functions f(x), derivatives and their orders, integral/memory "
        "kernels, and whether it is explicitly solvable for the target symbol. "
        "Call this BEFORE assigning any roles or type.",
        {"expression": str, "target_symbol": str},
    )
    async def analyze_expression(args):
        result = _analyze_expression(args.get("expression", ""),
                                     args.get("target_symbol", ""))
        trace.append({"tool": "analyze_expression", "input": args, "result": result})
        if verbose:
            print(f"      [spec] analyze_expression -> "
                  f"{result.get('classification_hint', 'err')}",
                  file=sys.stderr, flush=True)
        return {"content": [{"type": "text",
                             "text": json.dumps(result, ensure_ascii=False)}],
                "isError": not result.get("ok", True)}

    @tool(
        "check_substitution",
        "Substitute numeric values for parameters (and a test point for the "
        "independent variables / target) and report whether the expression "
        "evaluates to a finite real number. Use this to sanity-check the parameter "
        "values and ranges you intend to fix, so the data won't blow up or go complex.",
        {"expression": str, "assignments": dict, "target_symbol": str},
    )
    async def check_substitution(args):
        result = _check_substitution(args.get("expression", ""),
                                     args.get("assignments", {}) or {},
                                     args.get("target_symbol", ""))
        trace.append({"tool": "check_substitution", "input": args, "result": result})
        if verbose:
            print(f"      [spec] check_substitution -> "
                  f"{result.get('verdict', 'err')}", file=sys.stderr, flush=True)
        return {"content": [{"type": "text",
                             "text": json.dumps(result, ensure_ascii=False)}],
                "isError": not result.get("ok", True)}

    @tool(
        "excitation_check",
        "Forward-check that every additive term — and especially the NEW term this "
        "evolution step introduced (E minus its parent) — moves the dependent "
        "variable by at least k*sigma somewhere in your chosen sampling region. "
        "Pass the parameter values you intend to FIX (assignments), the independent-"
        "variable ranges (indep), and the noise sigma you will inject. For ODEs set "
        "is_ode=true (typed ODE records compare complete child and parent systems "
        "on the target trajectory, not only the raw target RHS). Use this to rebalance "
        "coefficients and pick the region "
        "where weak terms become visible, BEFORE emitting the spec.",
        {"assignments": dict, "indep": list, "sigma": float, "is_ode": bool},
    )
    async def excitation_check(args):
        result = _excitation_check(
            expression=expression,
            parent_expression=parent_expression,
            target_symbol=target_symbol,
            assignments=args.get("assignments", {}) or {},
            indep=args.get("indep", []) or [],
            sigma=args.get("sigma", 0.0),
            is_ode=bool(args.get("is_ode", False)),
            k=k_sigma,
            ode_contract=ode_contract,
            parent_ode_contract=parent_ode_contract,
        )
        trace.append({"tool": "excitation_check", "input": args, "result": result})
        if result.get("ok"):
            captured["excitation_ran"] = True
        if verbose:
            if result.get("mode") in {"ode", "ode_system"}:
                tag = f"new_term x{result.get('new_term_sigma_multiple')}"
            else:
                nt = (result.get("new_term") or {}).get("sigma_multiple")
                tag = f"new_term x{nt}; weak={len(result.get('weak_terms', []))}"
            print(f"      [spec] excitation_check -> {tag if result.get('ok') else 'err'}",
                  file=sys.stderr, flush=True)
        return {"content": [{"type": "text",
                             "text": json.dumps(result, ensure_ascii=False)}],
                "isError": not result.get("ok", True)}

    @tool(
        "auto_balance",
        "Numerically SOLVE the parameter values so every additive term — and the new "
        "term — reaches k*sigma, instead of hand-tuning. Give your starting "
        "assignments, the indep ranges, and sigma; it rescales each term's top-level "
        "linear coefficient by (k/current_multiple) and iterates. Returns tuned "
        "`assignments`, what `changed`, and whether it `converged`. CALL THIS FIRST to "
        "get a strong starting point; then use excitation_check to confirm. If it "
        "returns converged=false with terms still weak, those terms have NO top-level "
        "linear coefficient (e.g. the symbol sits inside tanh/exp, or terms are coupled "
        "through shared variables) — then move the sampling range toward where they are "
        "strongest, or, if no physical choice makes a term reach k*sigma, treat it as "
        "negligible and set excitation_ok=false. Explicit/implicit equations only.",
        {"assignments": dict, "indep": list, "sigma": float, "is_ode": bool},
    )
    async def auto_balance(args):
        result = _auto_balance(
            expression=expression,
            parent_expression=parent_expression,
            target_symbol=target_symbol,
            assignments=args.get("assignments", {}) or {},
            indep=args.get("indep", []) or [],
            sigma=args.get("sigma", 0.0),
            is_ode=bool(args.get("is_ode", False)),
            k=k_sigma,
            ode_contract=ode_contract,
            parent_ode_contract=parent_ode_contract,
        )
        trace.append({"tool": "auto_balance", "input": args,
                      "result": {kk: vv for kk, vv in result.items()
                                 if kk != "report"}})  # keep trace compact
        if verbose:
            if result.get("ok"):
                rep = result.get("report") or {}
                nw = len(rep.get("weak_terms", []))
                print(f"      [spec] auto_balance -> converged={result.get('converged')}"
                      f"; weak={nw}; changed={list(result.get('changed', {}))}",
                      file=sys.stderr, flush=True)
            else:
                print(f"      [spec] auto_balance -> err: {result.get('error')}",
                      file=sys.stderr, flush=True)
        return {"content": [{"type": "text",
                             "text": json.dumps(result, ensure_ascii=False)}],
                "isError": not result.get("ok", True)}

    @tool(
        "emit_data_gen_spec",
        "Submit the FINAL data-generation plan. Call this exactly once, after you "
        "have verified roles and type with the other tools. Calling this ends the task.",
        DataGenSpec.model_json_schema(),
    )
    async def emit_data_gen_spec(args):
        try:
            spec = DataGenSpec.model_validate(args)
            _validate_emitted_spec(spec, ode_contract=ode_contract)
        except Exception as e:
            trace.append({"tool": "emit_data_gen_spec", "validation_error": str(e)})
            return {"content": [{"type": "text",
                                 "text": f"SPEC VALIDATION FAILED: {type(e).__name__}: {e}. "
                                         f"Fix the fields and call emit_data_gen_spec again."}],
                    "isError": True}
        # Enforce the excitation step: don't accept a plan that never verified term
        # visibility. Only require it when there is a parent to compare against (so the
        # NEW term's effect is defined) and we reject at most once to avoid a deadlock.
        if (parent_expression and not captured["excitation_ran"]
                and not captured["emit_rejected"]):
            captured["emit_rejected"] = True
            trace.append({"tool": "emit_data_gen_spec",
                          "rejected": "excitation_check not run"})
            if verbose:
                print("      [spec] emit REJECTED -> run excitation_check first",
                      file=sys.stderr, flush=True)
            return {"content": [{"type": "text",
                                 "text": "NOT ACCEPTED YET: you have not verified term "
                                 "visibility. First call auto_balance (explicit/implicit) "
                                 "or excitation_check (is_ode=true for ODEs) to confirm "
                                 "every term — and the new term — reaches k*sigma, set the "
                                 "spec's `noise`, `excitation_ok` and `excitation_report` "
                                 "from what you find, then call emit_data_gen_spec again."}],
                    "isError": True}
        captured["spec"] = spec.model_dump()
        if verbose:
            print(f"      [spec] emit -> {spec.equation_type} -> {spec.integrator}",
                  file=sys.stderr, flush=True)
        return {"content": [{"type": "text", "text": "SPEC ACCEPTED."}]}

    srv = create_sdk_mcp_server(
        name="symspec", version="1.0.0",
        tools=[analyze_expression, check_substitution, excitation_check,
               auto_balance, emit_data_gen_spec],
    )

    parent_block = (f"{parent.get('target_symbol', target_symbol)} = {parent_expression}"
                    if parent_expression else
                    "(no parent provided — this is gen 0 / base, or the file had no "
                    "earlier generation; excitation_check will skip the new-term effect)")
    user_prompt = USER_TEMPLATE.format(
        discipline=discipline or "science",
        scenario_text=record.get("scenario_text", "(no scenario text)"),
        target_symbol=target_symbol,
        expression=expression,
        parent_block=parent_block,
        labels_block=_labels_block(record),
        range_hints=_range_hints(record),
        ode_contract_block=_ode_contract_block(ode_contract),
        sampling_replan_block=_sampling_replan_block(sampling_replan),
    )

    cli_path = cli_path or os.path.expanduser("~/.npm-global/bin/claude")
    # Only forward env vars that are actually set — an empty ANTHROPIC_API_KEY
    # would override ANTHROPIC_AUTH_TOKEN and break proxy auth.
    child_env = {"PATH": os.environ.get("PATH", "")}
    for k in ("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_API_KEY"):
        v = os.environ.get(k)
        if v:
            child_env[k] = v
    child_env.setdefault("ANTHROPIC_BASE_URL", "https://code.ppchat.vip")

    opts = ClaudeAgentOptions(
        model=model,
        system_prompt=SYSTEM_PROMPT.replace("{K}", f"{k_sigma:g}"),
        mcp_servers={"symspec": srv},
        allowed_tools=[
            "mcp__symspec__analyze_expression",
            "mcp__symspec__check_substitution",
            "mcp__symspec__excitation_check",
            "mcp__symspec__auto_balance",
            "mcp__symspec__emit_data_gen_spec",
        ],
        max_turns=max_turns,
        cli_path=cli_path if os.path.exists(cli_path) else None,
        env=child_env,
        **({"max_budget_usd": max_budget_usd} if max_budget_usd else {}),
    )

    result_msg = None
    sdk_err: str | None = None
    try:
        async for msg in query(prompt=user_prompt, options=opts):
            if isinstance(msg, AssistantMessage):
                for b in msg.content:
                    if isinstance(b, ToolUseBlock) and verbose:
                        pass  # tool execution is logged inside the tools themselves
                    elif isinstance(b, TextBlock):
                        pass
            elif isinstance(msg, ResultMessage):
                result_msg = msg
    except Exception as e:
        # The CLI raises a generic "success"/max-turns error when the agent runs
        # out of turns. That is not fatal if it already emitted a spec, or if it
        # made real progress we can salvage — only re-raise when we have nothing.
        sdk_err = f"{type(e).__name__}: {e}"
        trace.append({"sdk_error": sdk_err})
        if captured["spec"] is None and verbose:
            print(f"      [spec] SDK ended without emit ({sdk_err}); "
                  f"attempting salvage from trace", file=sys.stderr, flush=True)

    if captured["spec"] is None:
        raise SpecAgentError(
            f"agent finished without a valid spec"
            + (f" ({sdk_err})" if sdk_err else
               f" (turns={getattr(result_msg, 'num_turns', '?')})"),
            trace=trace)

    out = captured["spec"]
    out["_trace"] = trace
    if sdk_err:
        out["_sdk_warning"] = sdk_err
    if result_msg is not None:
        out["_cost_usd"] = getattr(result_msg, "total_cost_usd", None)
        out["_num_turns"] = getattr(result_msg, "num_turns", None)
    return out


def _openrouter_tool_definitions() -> list[dict[str, Any]]:
    """Describe the existing local math tools in OpenAI-compatible tool syntax."""
    scalar = {"type": "number"}
    indep_item = {
        "type": "object",
        "properties": {
            "symbol": {"type": "string"},
            "range": {"type": "array", "items": scalar, "minItems": 2, "maxItems": 2},
            "n_points": {"type": "integer"},
            "scale": {"type": "string", "enum": ["linear", "log"]},
        },
        "required": ["symbol", "range"],
    }
    spec_schema = {
        "type": "object",
        "properties": {
            "equation_type": {"type": "string", "enum": [
                "explicit", "implicit", "ode1", "ode_higher", "ode_system",
                "delay_differential", "integro_diff", "unsupported",
            ]},
            "integrator": {"type": "string", "enum": [
                "evaluate_explicit", "root_solve_implicit", "integrate_ode",
                "integrate_system", "integrate_dde", "integrate_basset", "unsupported",
            ]},
            "dependent_variable": {"type": "string"},
            "independent_variables": {"type": "array", "items": indep_item},
            "parameters": {"type": "array", "items": {
                "type": "object",
                "properties": {"symbol": {"type": "string"}, "value": scalar},
                "required": ["symbol", "value"],
            }},
            "rhs_for_integrator": {"type": "string"},
            "state_variables": {"type": "array", "items": {"type": "string"}},
            "state_rhs": {"type": "array", "items": {"type": "string"}},
            "initial_conditions": {"type": "object", "additionalProperties": scalar},
            "noise": scalar,
            "sanity_expectations": {"type": "array", "items": {"type": "string"}},
            "excitation_ok": {"type": "boolean"},
            "excitation_report": {"type": "string"},
            "role_corrections": {"type": "array", "items": {"type": "string"}},
            "rationale": {"type": "string"},
        },
        "required": [
            "equation_type", "integrator", "dependent_variable",
            "independent_variables", "parameters", "rhs_for_integrator",
        ],
    }

    def function(name: str, description: str, parameters: dict) -> dict[str, Any]:
        return {"type": "function", "function": {
            "name": name, "description": description, "parameters": parameters,
        }}

    return [
        function(
            "analyze_expression",
            "Parse a SymPy expression and return structural facts. Call this first "
            "before deciding equation type or roles.",
            {"type": "object", "properties": {
                "expression": {"type": "string"},
                "target_symbol": {"type": "string"},
            }, "required": ["expression", "target_symbol"]},
        ),
        function(
            "check_substitution",
            "Substitute numeric values and report whether the expression evaluates "
            "to a finite real number.",
            {"type": "object", "properties": {
                "expression": {"type": "string"},
                "assignments": {"type": "object", "additionalProperties": scalar},
                "target_symbol": {"type": "string"},
            }, "required": ["expression", "assignments", "target_symbol"]},
        ),
        function(
            "auto_balance",
            "For explicit or implicit equations, tune top-level coefficients so "
            "each term is visible above the noise. Call before excitation_check "
            "when applicable.",
            {"type": "object", "properties": {
                "assignments": {"type": "object", "additionalProperties": scalar},
                "indep": {"type": "array", "items": indep_item},
                "sigma": scalar,
                "is_ode": {"type": "boolean"},
            }, "required": ["assignments", "indep", "sigma", "is_ode"]},
        ),
        function(
            "excitation_check",
            "Check that all terms, especially the new term versus the parent, have "
            "a visible effect above k times the requested noise.",
            {"type": "object", "properties": {
                "assignments": {"type": "object", "additionalProperties": scalar},
                "indep": {"type": "array", "items": indep_item},
                "sigma": scalar,
                "is_ode": {"type": "boolean"},
            }, "required": ["assignments", "indep", "sigma", "is_ode"]},
        ),
        function(
            "emit_data_gen_spec",
            "Submit the final DataGenSpec exactly once after inspecting the equation "
            "and checking excitation. This ends the task when accepted.",
            spec_schema,
        ),
    ]


def plan_data_generation_openrouter(
    record: dict,
    discipline: str,
    *,
    model: str,
    parent: dict | None = None,
    sampling_replan: dict | None = None,
    k_sigma: float = 5.0,
    max_turns: int = 18,
    base_url: str | None = None,
    verbose: bool = True,
) -> dict:
    """Run the same DataSpec agent over OpenRouter-native function calling.

    Claude CLI is intentionally not involved here: it only understands Anthropic
    credentials/protocol. Python keeps the model-controlled tool loop, dispatches
    the same local tools, and records the same trace contract as the SDK path.
    """
    target_symbol = record.get("target_symbol", "y")
    expression = record.get("expression", "")
    if not expression:
        raise SpecAgentError("record has no 'expression'", trace=[])
    ode_contract = _ode_contract(record)
    parent_expression = (parent or {}).get("expression")
    parent_ode_contract = _ode_contract(parent) if parent is not None else None
    if sampling_replan and not sampling_replan.get("baseline_spec"):
        raise SpecAgentError("sampling_replan requires baseline_spec", trace=[])
    trace: list[dict] = []
    captured: dict[str, Any] = {
        "spec": None, "excitation_ran": False, "emit_rejected": False,
    }

    parent_block = (f"{parent.get('target_symbol', target_symbol)} = {parent_expression}"
                    if parent_expression else
                    "(no parent provided — this is gen 0 / base, or the file had no "
                    "earlier generation; excitation_check will skip the new-term effect)")
    user_prompt = USER_TEMPLATE.format(
        discipline=discipline or "science",
        scenario_text=record.get("scenario_text", "(no scenario text)"),
        target_symbol=target_symbol,
        expression=expression,
        parent_block=parent_block,
        labels_block=_labels_block(record),
        range_hints=_range_hints(record),
        ode_contract_block=_ode_contract_block(ode_contract),
        sampling_replan_block=_sampling_replan_block(sampling_replan),
    )

    def execute_tool(name: str, args: dict[str, Any]) -> str:
        """Run one deterministic local tool and serialize its result for the model."""
        try:
            if name == "analyze_expression":
                result = _analyze_expression(
                    args.get("expression", ""), args.get("target_symbol", ""),
                )
                trace.append({"tool": name, "input": args, "result": result})
                if verbose:
                    print(f"      [spec] analyze_expression -> "
                          f"{result.get('classification_hint', 'err')}",
                          file=sys.stderr, flush=True)
                return json.dumps(result, ensure_ascii=False)

            if name == "check_substitution":
                result = _check_substitution(
                    args.get("expression", ""), args.get("assignments", {}) or {},
                    args.get("target_symbol", ""),
                )
                trace.append({"tool": name, "input": args, "result": result})
                if verbose:
                    print(f"      [spec] check_substitution -> "
                          f"{result.get('verdict', 'err')}", file=sys.stderr, flush=True)
                return json.dumps(result, ensure_ascii=False)

            if name == "auto_balance":
                result = _auto_balance(
                    expression=expression,
                    parent_expression=parent_expression,
                    target_symbol=target_symbol,
                    assignments=args.get("assignments", {}) or {},
                    indep=args.get("indep", []) or [],
                    sigma=args.get("sigma", 0.0),
                    is_ode=bool(args.get("is_ode", False)),
                    k=k_sigma,
                    ode_contract=ode_contract,
                    parent_ode_contract=parent_ode_contract,
                )
                trace.append({"tool": name, "input": args,
                              "result": {k: v for k, v in result.items() if k != "report"}})
                if verbose:
                    print(f"      [spec] auto_balance -> "
                          f"converged={result.get('converged')}; "
                          f"changed={list(result.get('changed', {}))}",
                          file=sys.stderr, flush=True)
                return json.dumps(result, ensure_ascii=False)

            if name == "excitation_check":
                result = _excitation_check(
                    expression=expression,
                    parent_expression=parent_expression,
                    target_symbol=target_symbol,
                    assignments=args.get("assignments", {}) or {},
                    indep=args.get("indep", []) or [],
                    sigma=args.get("sigma", 0.0),
                    is_ode=bool(args.get("is_ode", False)),
                    k=k_sigma,
                    ode_contract=ode_contract,
                    parent_ode_contract=parent_ode_contract,
                )
                trace.append({"tool": name, "input": args, "result": result})
                if result.get("ok"):
                    captured["excitation_ran"] = True
                if verbose:
                    print(f"      [spec] excitation_check -> "
                          f"{'ok' if result.get('ok') else result.get('error', 'err')}",
                          file=sys.stderr, flush=True)
                return json.dumps(result, ensure_ascii=False)

            if name == "emit_data_gen_spec":
                try:
                    spec = DataGenSpec.model_validate(args)
                    _validate_emitted_spec(spec, ode_contract=ode_contract)
                except Exception as exc:
                    msg = f"SPEC VALIDATION FAILED: {type(exc).__name__}: {exc}"
                    trace.append({"tool": name, "validation_error": str(exc)})
                    return json.dumps({"ok": False, "error": msg}, ensure_ascii=False)
                if (parent_expression and not captured["excitation_ran"]
                        and not captured["emit_rejected"]):
                    captured["emit_rejected"] = True
                    msg = "NOT ACCEPTED YET: call excitation_check before emitting the spec."
                    trace.append({"tool": name, "rejected": "excitation_check not run"})
                    if verbose:
                        print("      [spec] emit REJECTED -> run excitation_check first",
                              file=sys.stderr, flush=True)
                    return json.dumps({"ok": False, "error": msg}, ensure_ascii=False)
                captured["spec"] = spec.model_dump()
                trace.append({"tool": name, "accepted": True})
                if verbose:
                    print(f"      [spec] emit -> {spec.equation_type} -> {spec.integrator}",
                          file=sys.stderr, flush=True)
                return json.dumps({"ok": True, "message": "SPEC ACCEPTED."})

            msg = f"Unknown tool '{name}'."
            trace.append({"tool": name, "error": msg})
            return json.dumps({"ok": False, "error": msg})
        except Exception as exc:
            msg = f"{type(exc).__name__}: {exc}"
            trace.append({"tool": name, "input": args, "error": msg})
            return json.dumps({"ok": False, "error": msg}, ensure_ascii=False)

    caller = build_model_caller("openrouter", base_url=base_url)
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT.replace("{K}", f"{k_sigma:g}")},
        {"role": "user", "content": user_prompt},
    ]
    tools = _openrouter_tool_definitions()
    for turn in range(1, max_turns + 1):
        try:
            payload = caller.openrouter_chat(
                messages=messages, model=model, max_tokens=4000, tools=tools,
            )
            message = payload["choices"][0]["message"]
        except (KeyError, IndexError, TypeError, ModelRequestError) as exc:
            raise SpecAgentError(f"OpenRouter agent request failed: {exc}", trace=trace) from exc

        content = message.get("content")
        tool_calls = message.get("tool_calls") or []
        trace.append({"turn": turn, "assistant_content": content,
                      "tool_calls": [{"name": c.get("function", {}).get("name"),
                                      "id": c.get("id")} for c in tool_calls]})
        assistant_message: dict[str, Any] = {"role": "assistant"}
        if content is not None:
            assistant_message["content"] = content
        if tool_calls:
            assistant_message["tool_calls"] = tool_calls
        messages.append(assistant_message)

        if not tool_calls:
            if captured["spec"] is not None:
                out = captured["spec"]
                out.update({"_trace": trace, "_provider": "openrouter", "_num_turns": turn})
                return out
            raise SpecAgentError(
                "OpenRouter agent stopped without calling emit_data_gen_spec",
                trace=trace,
            )

        for call in tool_calls:
            function = call.get("function") or {}
            name = function.get("name", "")
            raw_args = function.get("arguments", "{}")
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                if not isinstance(args, dict):
                    raise ValueError("tool arguments must be an object")
            except (json.JSONDecodeError, ValueError) as exc:
                result = json.dumps({"ok": False, "error": f"invalid tool arguments: {exc}"})
                trace.append({"tool": name, "raw_arguments": raw_args, "error": str(exc)})
            else:
                result = execute_tool(name, args)
            messages.append({"role": "tool", "tool_call_id": call.get("id", ""),
                             "content": result})

        if captured["spec"] is not None:
            out = captured["spec"]
            out.update({"_trace": trace, "_provider": "openrouter", "_num_turns": turn})
            return out

    raise SpecAgentError(
        f"OpenRouter agent hit max_turns ({max_turns}) without a valid spec", trace=trace,
    )


def plan_data_generation(
    record: dict,
    discipline: str,
    *,
    provider: str = "anthropic",
    base_url: str | None = None,
    auth_source: str = "auto",
    **kwargs,
) -> dict:
    """Run either the original Claude CLI Agent or the OpenRouter tool loop."""
    if provider == "openrouter":
        # The OpenRouter loop has no Claude CLI, so drop CLI-only arguments.
        kwargs.pop("cli_path", None)
        return plan_data_generation_openrouter(
            record, discipline, base_url=base_url, **kwargs,
        )
    if provider != "anthropic":
        raise ValueError(f"Unsupported provider: {provider}")
    # auth_source is accepted for CLI parity; CLI authentication remains env-driven.
    del base_url, auth_source
    return asyncio.run(plan_data_generation_async(record, discipline, **kwargs))


# ============================================================
# Demo equation (gen2 sphere-in-fluid ODE, deliberately mislabeled
# roles, so you can see the agent CORRECT them).
# ============================================================

DEMO_RECORD = {
    "base_id": "demo_sphere",
    "generation": 2,
    "target_symbol": "v",
    "scenario_text": (
        "A small solid sphere is released from rest in a viscous fluid and "
        "accelerates under gravity, buoyancy, linear drag, and added mass."
    ),
    "expression": "((m - rho_f*V_s)*g - b*v) / (m + C_a*rho_f*V_s)",
    "symbols": ["v", "m", "b", "g", "rho_f", "V_s", "C_a"],
    "symbol_descriptions": [
        "sphere velocity", "mass", "drag coeff", "gravity",
        "fluid density", "sphere volume", "added-mass coeff",
    ],
    "symbol_properties": ["P", "P", "P", "P", "P", "P", "P"],
    "new_symbol_range_suggestions": {"C_a": "[0, 1]", "b": "[0.1, 2]"},
}


# ============================================================
# CLI
# ============================================================

def _load_records(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Input not found: {path}")
    if path.suffix == ".jsonl":
        out = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def _match_id(r: dict, want: str) -> bool:
    return want in (r.get("scenario_id"), r.get("id"), r.get("base_id"))


def _upgrade_ode_specs(spec_path: Path, evolved_path: Path, output_path: Path) -> int:
    """Add derivative-label metadata to old Specs without calling an LLM."""
    evolved = _load_records(evolved_path)
    if not evolved:
        raise SystemExit("Evolved-equation file is empty.")
    by_generation = {record.get("generation"): record for record in evolved}
    upgraded = []
    for spec in _load_records(spec_path):
        if "error" not in spec and spec.get("equation_type") == "ode_system":
            record = by_generation.get(spec.get("generation"), evolved[-1])
            spec = _attach_ode_benchmark_metadata(spec, record)
        upgraded.append(spec)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for spec in upgraded:
            f.write(json.dumps(spec, ensure_ascii=False) + "\n")
    return len(upgraded)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Stage 6a: plan data generation with Claude CLI or OpenRouter tools.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--input", help="evolution/equations .jsonl or .json")
    p.add_argument("--id", default=None, help="only this scenario_id/id/base_id")
    p.add_argument("--generation", type=int, default=None,
                   help="when --id matches several generations, pick this one")
    p.add_argument("--last", action="store_true",
                   help="only the LAST record in the file (the final evolved "
                        "equation). Applied after --id/--generation filtering.")
    p.add_argument("--discipline", default=None)
    p.add_argument("--model", default="claude-opus-4-7")
    p.add_argument("--provider", choices=["anthropic", "openrouter"],
                   default="anthropic",
                   help="anthropic uses Claude CLI Agent; openrouter uses Python tool loop")
    p.add_argument("--base-url", default=None,
                   help="Provider base URL. Defaults to the selected provider's environment value")
    p.add_argument("--auth-source", choices=["auto", "api_key", "auth_token"],
                   default="auto",
                   help="Accepted for CLI parity; only used by direct API providers")
    p.add_argument("--k-sigma", type=float, default=5.0,
                   help="visibility threshold: every term (and the new term vs the "
                        "parent) must move the data by >= k*noise somewhere in the "
                        "sampled region")
    p.add_argument("--cli-path", default=None,
                   help="path to claude CLI; ignored with --provider openrouter")
    p.add_argument("--max-turns", type=int, default=18,
                   help="maximum model/tool turns for the agent loop")
    p.add_argument("--output", default=None,
                   help="write specs to this .jsonl (default: "
                        "outputs/Specs/<input-stem>_spec.jsonl)")
    p.add_argument("--upgrade-spec", default=None,
                   help="existing Spec JSONL to upgrade with ODE derivative-label metadata; no API call")
    p.add_argument("--evolved", default=None,
                   help="matching Evolved_Equations JSONL; required with --upgrade-spec")
    p.add_argument("--demo", action="store_true",
                   help="run the built-in mislabeled demo equation")
    args = p.parse_args()

    if args.upgrade_spec:
        if not args.evolved or not args.output:
            raise SystemExit("--upgrade-spec requires --evolved and --output.")
        count = _upgrade_ode_specs(
            Path(args.upgrade_spec), Path(args.evolved), Path(args.output),
        )
        print(f"Wrote {count} upgraded Spec record(s) to {args.output}", file=sys.stderr)
        return

    if not args.demo and not args.input:
        raise SystemExit("Provide --input <file> or --demo.")

    if args.provider == "openrouter":
        if not os.environ.get("OPENROUTER_API_KEY"):
            raise SystemExit("Missing OPENROUTER_API_KEY.")
    elif not (os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY")):
        raise SystemExit("Missing ANTHROPIC_AUTH_TOKEN (or ANTHROPIC_API_KEY).")

    parent_of: dict[int, dict] = {}
    if args.demo:
        records = [DEMO_RECORD]
    else:
        all_records = [r for r in _load_records(Path(args.input)) if r.get("expression")]
        # Build parent links BEFORE filtering: within each scenario lineage, order by
        # generation; each record's parent is the previous generation. Keyed by id()
        # so the link survives the --id/--last filtering below.
        by_scenario: dict[str, list[dict]] = {}
        for r in all_records:
            key = r.get("scenario_id") or r.get("base_id") or r.get("id") or "_"
            by_scenario.setdefault(key, []).append(r)
        for lineage in by_scenario.values():
            lineage.sort(key=lambda r: (r.get("generation") if r.get("generation")
                                        is not None else 0))
            for prev, cur in zip(lineage, lineage[1:]):
                parent_of[id(cur)] = prev

        records = all_records
        if args.id:
            records = [r for r in records if _match_id(r, args.id)]
            if args.generation is not None:
                records = [r for r in records if r.get("generation") == args.generation]
        if not records:
            raise SystemExit("No matching records with an 'expression'.")
        if args.last:
            records = records[-1:]  # final evolved equation only

    specs = []
    for i, r in enumerate(records, 1):
        discipline = args.discipline or r.get("discipline") or "science"
        rid = r.get("scenario_id") or r.get("id") or r.get("base_id") or f"rec{i}"
        print(f"\n[{i}/{len(records)}] {rid} (gen {r.get('generation','?')})",
              file=sys.stderr, flush=True)
        print(f"    {r.get('target_symbol','?')} = {r.get('expression','')}",
              file=sys.stderr)
        parent = parent_of.get(id(r))
        if parent is not None:
            print(f"    parent (gen {parent.get('generation','?')}): "
                  f"{parent.get('expression','')[:70]}", file=sys.stderr)
        try:
            spec = plan_data_generation(
                r, discipline,
                provider=args.provider,
                base_url=args.base_url,
                auth_source=args.auth_source,
                model=args.model,
                cli_path=args.cli_path,
                parent=parent,
                k_sigma=args.k_sigma,
                max_turns=args.max_turns,
            )
            spec = _attach_ode_benchmark_metadata(spec, r)
        except SpecAgentError as e:
            print(f"    FAILED: {e}", file=sys.stderr)
            spec = {"error": str(e), "_trace": e.trace}
        spec["record_id"] = rid
        spec["generation"] = r.get("generation")
        specs.append(spec)

        if "error" not in spec:
            print(f"    type        : {spec['equation_type']} -> {spec['integrator']}",
                  file=sys.stderr)
            print(f"    dependent   : {spec['dependent_variable']}", file=sys.stderr)
            print(f"    independent : "
                  f"{[v['symbol'] for v in spec['independent_variables']]}",
                  file=sys.stderr)
            print(f"    parameters  : "
                  f"{ {pp['symbol']: pp['value'] for pp in spec['parameters']} }",
                  file=sys.stderr)
            if spec.get("role_corrections"):
                print(f"    corrections : {spec['role_corrections']}", file=sys.stderr)

    # Resolve output path: explicit --output wins; else default under outputs/Specs/.
    out_path = None
    if args.output:
        out_path = Path(args.output)
    elif not args.demo:
        stem = Path(args.input).stem
        if args.last:
            stem += "_last"
        out_path = Path(__file__).resolve().parent / "outputs" / "Specs" / f"{stem}_spec.jsonl"

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            for s in specs:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        print(f"\nWrote {len(specs)} spec(s) to {out_path}", file=sys.stderr)
    elif args.demo:
        print("\n--- DataGenSpec ---", file=sys.stderr)
        print(json.dumps({k: v for k, v in specs[0].items() if not k.startswith("_")},
                         ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
