"""
Stage 6b — Deterministic data generator (spec -> CSV).
======================================================

Read ONE `DataGenSpec` (the output of Stage 6a, `data_spec_agent_sdk.py`) and
actually compute the data points. This stage is PURE numpy/scipy: no LLM, fully
deterministic and reproducible. The agent decided *what* and *how*; here we just
execute that plan and write a CSV.

Dispatch by `spec["integrator"]`:
    evaluate_explicit    -> lambdify the RHS, evaluate on the (multi-axis) grid of
                            independent variables. Handles y = f(x1, x2, ...).
    root_solve_implicit  -> for each grid point, solve g(dep, x..., params) = 0 for
                            the dependent variable with scipy.optimize.fsolve.
    integrate_ode        -> dy/dt = rhs, single time axis, scipy solve_ivp.
    integrate_system     -> first-order system (state_variables / state_rhs),
                            solve_ivp; also used for reduced higher-order ODEs.
    integrate_dde        -> scalar first-order constant-delay DDE, integrated with
                            method-of-steps RK4 and a constant pre-history.
    integrate_basset     -> integro-differential (memory kernel): delegated to the
                            project's integrate_basset module if the shape matches,
                            else reported as unsupported.

The CSV columns are: every independent variable, then the dependent variable, then
(optionally) a `<dep>_noisy` column when spec["noise"] > 0.

Usage
-----
    python generate_from_spec.py --spec specs/....jsonl
    python generate_from_spec.py --spec specs/....jsonl --output-dir outputs/foo
    python generate_from_spec.py --spec one_spec.json --index 0
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np


# ============================================================
# Safe sympy parsing — same reserved-symbol guard as Stage 6a,
# so `S`, `I`, `E`, ... stay plain variables, not sympy singletons.
# ============================================================

_RESERVED_FUNCS = {
    "Abs", "Max", "Min", "Piecewise", "Heaviside", "Derivative", "Integral",
    "sin", "cos", "tan", "asin", "acos", "atan", "atan2", "sinh", "cosh",
    "tanh", "asinh", "acosh", "atanh", "exp", "log", "ln", "sqrt", "sign",
    "floor", "ceiling", "pi",
}


def _symbols_in(expression: str) -> set[str]:
    import re
    return set(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", expression))


def _called_names(expression: str) -> set[str]:
    import re
    return set(re.findall(r"\b([A-Za-z_][A-Za-z_0-9]*)\s*\(", expression))


def _check_parentheses(expression: str) -> None:
    """Give malformed model output a deterministic, actionable parse error."""
    depth = 0
    for index, char in enumerate(expression):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                raise ValueError(f"unmatched ')' at character {index}")
    if depth:
        raise ValueError(f"{depth} unmatched '(' character(s)")


def _local_symbol_map(expression: str, *extra_names: str,
                      force_symbols: set[str] | None = None) -> dict:
    """Map names in the expression to plain sympy Symbols.

    `force_symbols` (the spec's declared parameters / variables / dependent name)
    are ALWAYS made Symbols, even if they collide with a reserved function name
    (e.g. a parameter literally called `gamma` must not become the Gamma function).
    Other names fall back to Symbols unless they are reserved math functions.
    """
    import sympy
    force = set(force_symbols or ())
    names = _symbols_in(expression) | set(extra_names) | force
    called = _called_names(expression) - _RESERVED_FUNCS
    local = {n: sympy.Symbol(n) for n in names
             if (n in force or n not in _RESERVED_FUNCS) and n not in called}
    # Preserve unrecognised f(t)-style names as SymPy functions for DDE parsing.
    local.update({n: sympy.Function(n) for n in called})
    return local


def _lambdify(expression: str, arg_names: list[str],
              force_symbols: set[str] | None = None):
    """Compile `expression` into a numpy function f(*args) over arg_names (in order)."""
    import sympy
    _check_parentheses(expression)
    local = _local_symbol_map(expression, *arg_names, force_symbols=force_symbols)
    expr = sympy.sympify(expression, locals=local)
    syms = [sympy.Symbol(n) for n in arg_names]
    f = sympy.lambdify(syms, expr, modules="numpy")
    return f, expr


# ============================================================
# Spec accessors
# ============================================================

def _indep(spec: dict) -> list[dict]:
    return spec.get("independent_variables", []) or []


def _params(spec: dict) -> dict[str, float]:
    return {p["symbol"]: float(p["value"]) for p in spec.get("parameters", [])}


def _declared_symbols(spec: dict) -> set[str]:
    """Every symbol the spec names — params, independent vars, dependent var, and
    state vars. These are forced to plain Symbols at parse time so a parameter that
    happens to share a name with a sympy function (gamma, beta, ...) is never
    reinterpreted as that function."""
    names = set(_params(spec).keys())
    names |= {iv["symbol"] for iv in _indep(spec)}
    if spec.get("dependent_variable"):
        names.add(spec["dependent_variable"])
    names |= set(spec.get("state_variables", []) or [])
    return names


def _axis_grid(iv: dict) -> np.ndarray:
    lo, hi = iv["range"]
    n = int(iv.get("n_points", 200))
    scale = iv.get("scale", "linear")
    if scale == "log":
        if lo <= 0:
            raise SystemExit(f"log scale needs positive range, got {iv['range']} "
                             f"for '{iv['symbol']}'")
        return np.logspace(np.log10(lo), np.log10(hi), n)
    return np.linspace(lo, hi, n)


def _sample_axes(ivs: list[dict], n_total: int | None, seed: int) -> list[np.ndarray]:
    """Build the flat design matrix (one 1-D array per independent variable).

    - n_total given AND >=2 variables  -> draw n_total RANDOM points in the box
      (uniform per axis, log-uniform for log scale). Avoids the Cartesian blow-up
      that makes a per-axis grid useless in high dimensions.
    - otherwise (1 variable, or no n_total) -> Cartesian product of per-axis grids
      (for a single axis this is just that axis), preserving the old behaviour.
    """
    if n_total and len(ivs) >= 2:
        rng = np.random.default_rng(seed)
        cols = []
        for iv in ivs:
            lo, hi = iv["range"]
            if iv.get("scale") == "log":
                if lo <= 0:
                    raise SystemExit(f"log scale needs positive range for '{iv['symbol']}'")
                cols.append(10 ** rng.uniform(np.log10(lo), np.log10(hi), n_total))
            else:
                cols.append(rng.uniform(lo, hi, n_total))
        return cols
    # grid path
    if n_total and len(ivs) == 1:
        ivs = [dict(ivs[0], n_points=n_total)]
    axes = [_axis_grid(iv) for iv in ivs]
    mesh = np.meshgrid(*axes, indexing="ij") if axes else []
    return [m.ravel() for m in mesh] if mesh else []


def _add_noise(y: np.ndarray, noise: float, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    # DataGenSpec defines noise as an absolute dependent-variable standard deviation.
    return y + rng.normal(0.0, noise, size=y.shape)


# ============================================================
# Generators, one per integrator
# ============================================================

def gen_evaluate_explicit(spec: dict, seed: int) -> tuple[list[str], np.ndarray]:
    """y = f(x1, x2, ...). Single var -> grid; multi-var with n_total -> random box."""
    ivs = _indep(spec)
    if not ivs:
        raise SystemExit("evaluate_explicit needs >=1 independent variable")
    params = _params(spec)
    dep = spec["dependent_variable"]
    rhs = spec["rhs_for_integrator"]

    axis_names = [iv["symbol"] for iv in ivs]
    n_total = spec.get("_n_total")

    # arg order: independent vars first, then parameters.
    param_names = list(params.keys())
    f, _ = _lambdify(rhs, axis_names + param_names,
                     force_symbols=_declared_symbols(spec))

    flat_axes = _sample_axes(ivs, n_total, seed)
    pvals = [np.full(flat_axes[0].shape, params[p]) for p in param_names]
    y = np.asarray(f(*flat_axes, *pvals), dtype=float)
    y = np.broadcast_to(y, flat_axes[0].shape).astype(float)

    cols = axis_names + [dep]
    data = flat_axes + [y]
    noise = float(spec.get("noise", 0.0) or 0.0)
    if noise > 0:
        data.append(_add_noise(y, noise, seed))
        cols.append(f"{dep}_noisy")
    return cols, np.column_stack(data)


def gen_root_solve_implicit(spec: dict, seed: int) -> tuple[list[str], np.ndarray]:
    """Solve g(dep, x..., params) = 0 for the dependent variable at each grid point."""
    from scipy.optimize import fsolve

    ivs = _indep(spec)
    params = _params(spec)
    dep = spec["dependent_variable"]
    rhs = spec["rhs_for_integrator"]  # the g(...) whose root we seek

    axis_names = [iv["symbol"] for iv in ivs]
    param_names = list(params.keys())

    # g as a function of (dep, axes..., params...)
    g, _ = _lambdify(rhs, [dep] + axis_names + param_names,
                     force_symbols=_declared_symbols(spec))
    pv = [params[p] for p in param_names]

    flat_axes = _sample_axes(ivs, spec.get("_n_total"), seed)
    n_pts = flat_axes[0].shape[0] if flat_axes else 1

    y = np.empty(n_pts, dtype=float)
    guess = 1.0
    for k in range(n_pts):
        xs = [fa[k] for fa in flat_axes]
        root = fsolve(lambda d: g(d[0], *xs, *pv), x0=[guess], full_output=False)
        y[k] = root[0]
        guess = root[0]  # warm-start the next point for continuity

    cols = axis_names + [dep]
    data = (flat_axes if flat_axes else []) + [y]
    noise = float(spec.get("noise", 0.0) or 0.0)
    if noise > 0:
        data.append(_add_noise(y, noise, seed))
        cols.append(f"{dep}_noisy")
    return cols, np.column_stack(data)


def _time_axis(spec: dict) -> dict:
    """Pick the single time-like independent variable for an ODE."""
    ivs = _indep(spec)
    if not ivs:
        raise SystemExit("ODE integrator needs an independent (time) variable")
    # Prefer one literally named t / time; else the first axis.
    for iv in ivs:
        if iv["symbol"] in ("t", "time", "tau", "x"):
            return iv
    return ivs[0]


def gen_integrate_ode(spec: dict, seed: int) -> tuple[list[str], np.ndarray]:
    """First-order ODE  d(dep)/d(axis) = rhs(axis, dep, params), via solve_ivp."""
    from scipy.integrate import solve_ivp

    params = _params(spec)
    dep = spec["dependent_variable"]
    rhs = spec["rhs_for_integrator"]
    tv = _time_axis(spec)
    tname = tv["symbol"]
    lo, hi = tv["range"]
    n = int(spec.get("_n_total") or tv.get("n_points", 200))

    param_names = list(params.keys())
    f, _ = _lambdify(rhs, [tname, dep] + param_names,
                     force_symbols=_declared_symbols(spec))
    pv = [params[p] for p in param_names]

    y0 = float(spec.get("initial_conditions", {}).get(dep, 0.0))
    t_eval = np.linspace(lo, hi, n)
    sol = solve_ivp(
        fun=lambda tt, yy: [float(f(tt, yy[0], *pv))],
        t_span=(lo, hi), y0=[y0], t_eval=t_eval,
        method="RK45", rtol=1e-8, atol=1e-10,
    )
    if not sol.success:
        raise SystemExit(f"ODE integration failed: {sol.message}")

    t, y = sol.t, sol.y[0]
    cols = [tname, dep]
    data = [t, y]
    noise = float(spec.get("noise", 0.0) or 0.0)
    if noise > 0:
        data.append(_add_noise(y, noise, seed))
        cols.append(f"{dep}_noisy")
    return cols, np.column_stack(data)


def _compile_scalar_dde(spec: dict):
    """Compile dy/dt = f(t, y(t), y(t-delay_1), ...) from a DataGenSpec.

    Only retarded, constant-delay scalar DDEs are accepted. An ungoverned second
    state such as h(t) must have a state equation; it is not silently frozen.
    """
    import sympy
    from sympy.core.function import AppliedUndef

    params = _params(spec)
    dep = spec["dependent_variable"]
    tname = _time_axis(spec)["symbol"]
    rhs = spec["rhs_for_integrator"]
    _check_parentheses(rhs)

    force = _declared_symbols(spec) - {dep}
    local = _local_symbol_map(rhs, tname, force_symbols=force)
    local[dep] = sympy.Function(dep)
    expr = sympy.sympify(rhs, locals=local)

    applied = list(expr.atoms(AppliedUndef))
    unknown = sorted({str(call) for call in applied if call.func.__name__ != dep})
    if unknown:
        raise ValueError(
            "integrate_dde only supports one dynamic state; missing equations for "
            + ", ".join(unknown)
        )

    calls = [call for call in applied if call.func.__name__ == dep]
    if not calls:
        raise ValueError(f"integrate_dde expected at least one {dep}({tname}) term")

    t_symbol = sympy.Symbol(tname)
    param_subs = {sympy.Symbol(name): value for name, value in params.items()}
    call_delays: dict[object, float] = {}
    for call in calls:
        if len(call.args) != 1:
            raise ValueError(f"unsupported state call '{call}'; expected one time argument")
        delay_expr = sympy.simplify((t_symbol - call.args[0]).subs(param_subs))
        if delay_expr.free_symbols:
            raise ValueError(
                f"delay in '{call}' is not a fixed numeric constant: {delay_expr}"
            )
        delay = float(delay_expr)
        if abs(delay) < 1e-12:
            delay = 0.0
        if delay < 0:
            raise ValueError(f"advanced state '{call}' is not a retarded DDE")
        call_delays[call] = delay

    delays = sorted({delay for delay in call_delays.values() if delay > 0.0})
    if not delays:
        raise ValueError(
            "integrate_dde requires a positive constant delay such as y(t - tau)"
        )

    current = sympy.Symbol("__dde_current__")
    delay_symbols = {
        delay: sympy.Symbol(f"__dde_delay_{index}__")
        for index, delay in enumerate(delays)
    }
    replacements = {
        call: current if delay == 0.0 else delay_symbols[delay]
        for call, delay in call_delays.items()
    }
    compiled_expr = expr.xreplace(replacements).subs(param_subs)
    allowed = {t_symbol, current, *delay_symbols.values()}
    residual = compiled_expr.free_symbols - allowed
    if residual:
        raise ValueError(
            "unassigned symbols after parameter substitution: "
            + ", ".join(sorted(str(symbol) for symbol in residual))
        )
    f = sympy.lambdify([t_symbol, current, *delay_symbols.values()],
                        compiled_expr, modules="numpy")
    return f, delays


def gen_integrate_dde(spec: dict, seed: int) -> tuple[list[str], np.ndarray]:
    """Integrate a scalar constant-delay DDE by method-of-steps RK4.

    The declared initial value defines the pre-history, y(t < t0) = y0. The
    internal grid resolves each shortest delay with at least four RK steps, then
    the result is resampled to the requested output points.
    """
    dep = spec["dependent_variable"]
    tv = _time_axis(spec)
    tname = tv["symbol"]
    lo, hi = tv["range"]
    n_out = int(spec.get("_n_total") or tv.get("n_points", 200))
    if hi <= lo:
        raise SystemExit(f"DDE time range must increase, got {tv['range']}")
    if n_out < 2:
        raise SystemExit("integrate_dde needs at least two output points")

    f, delays = _compile_scalar_dde(spec)
    y0 = float(spec.get("initial_conditions", {}).get(dep, 0.0))
    min_delay = min(delays)
    requested_step = (hi - lo) / (n_out - 1)
    internal_step = min(requested_step, min_delay / 4.0)
    n_internal = max(1, int(np.ceil((hi - lo) / internal_step)))
    t_internal = np.linspace(lo, hi, n_internal + 1)
    step = t_internal[1] - t_internal[0]
    y_internal = np.empty(n_internal + 1, dtype=float)
    y_internal[0] = y0

    for index in range(n_internal):
        t0 = t_internal[index]
        y_now = y_internal[index]

        def history(query: float) -> float:
            if query <= lo:
                return y0
            # step <= min_delay/4 ensures this never asks for future values.
            return float(np.interp(query, t_internal[:index + 1],
                                   y_internal[:index + 1]))

        def rhs(time: float, state: float) -> float:
            delayed = [history(time - delay) for delay in delays]
            value = float(f(time, state, *delayed))
            if not np.isfinite(value):
                raise FloatingPointError(
                    f"DDE RHS became non-finite at t={time:.8g}, y={state:.8g}"
                )
            return value

        k1 = rhs(t0, y_now)
        k2 = rhs(t0 + step / 2.0, y_now + step * k1 / 2.0)
        k3 = rhs(t0 + step / 2.0, y_now + step * k2 / 2.0)
        k4 = rhs(t0 + step, y_now + step * k3)
        y_internal[index + 1] = y_now + step * (k1 + 2 * k2 + 2 * k3 + k4) / 6.0
        if not np.isfinite(y_internal[index + 1]):
            raise FloatingPointError(
                f"DDE solution became non-finite at t={t_internal[index + 1]:.8g}"
            )

    t_out = np.linspace(lo, hi, n_out)
    y_out = np.interp(t_out, t_internal, y_internal)
    cols = [tname, dep]
    data = [t_out, y_out]
    noise = float(spec.get("noise", 0.0) or 0.0)
    if noise > 0:
        data.append(_add_noise(y_out, noise, seed))
        cols.append(f"{dep}_noisy")
    return cols, np.column_stack(data)


def gen_integrate_system(spec: dict, seed: int) -> tuple[list[str], np.ndarray]:
    """First-order system from state_variables / state_rhs, via solve_ivp.

    Output columns: time, then every state variable. For typed pipeline ODEs,
    append the benchmark derivative target and its noisy observation.
    """
    from scipy.integrate import solve_ivp

    states = spec.get("state_variables", []) or []
    rhss = spec.get("state_rhs", []) or []
    if not states or len(states) != len(rhss):
        raise SystemExit("integrate_system needs aligned state_variables/state_rhs")

    params = _params(spec)
    dep = spec["dependent_variable"]
    tv = _time_axis(spec)
    tname = tv["symbol"]
    lo, hi = tv["range"]
    n = int(spec.get("_n_total") or tv.get("n_points", 500))
    param_names = list(params.keys())
    pv = [params[p] for p in param_names]

    compiled = [_lambdify(e, [tname] + states + param_names,
                          force_symbols=_declared_symbols(spec))[0] for e in rhss]
    ic = spec.get("initial_conditions", {})
    y0 = [float(ic.get(s, 0.0)) for s in states]

    def system(tt, Y):
        return [float(f(tt, *Y, *pv)) for f in compiled]

    t_eval = np.linspace(lo, hi, n)
    sol = solve_ivp(fun=system, t_span=(lo, hi), y0=y0, t_eval=t_eval,
                    method="RK45", rtol=1e-8, atol=1e-10)
    if not sol.success:
        raise SystemExit(f"system integration failed: {sol.message}")

    cols = [tname] + states
    data = [sol.t] + [sol.y[i] for i in range(len(states))]
    benchmark_output = spec.get("benchmark_output")
    benchmark_state = spec.get("benchmark_target_state")
    if benchmark_output and benchmark_state in states:
        target_idx = states.index(benchmark_state)
        derivative = np.asarray([
            compiled[target_idx](time, *sol.y[:, col], *pv)
            for col, time in enumerate(sol.t)
        ], dtype=float)
        data.append(derivative)
        cols.append(benchmark_output)
        noise = float(spec.get("noise", 0.0) or 0.0)
        if noise > 0:
            data.append(_add_noise(derivative, noise, seed))
            cols.append(f"{benchmark_output}_noisy")
        return cols, np.column_stack(data)

    # Legacy Specs have no explicit derivative benchmark metadata.
    noise = float(spec.get("noise", 0.0) or 0.0)
    if noise > 0 and dep in states:
        idx = states.index(dep)
        data.append(_add_noise(sol.y[idx], noise, seed))
        cols.append(f"{dep}_noisy")
    return cols, np.column_stack(data)


def gen_integrate_basset(spec: dict, seed: int) -> tuple[list[str], np.ndarray]:
    """Integro-differential equation with a Basset (1/sqrt(t-tau)) memory kernel.

    Generic, spec-driven solver. We do NOT hard-wire any drag model. Instead we
    split the spec's RHS  dv/dt = F(t, v, history)  into

        dv/dt = local(t, v)  +  cB * INT_0^t v'(tau)/sqrt(t-tau) dtau

    by symbolically isolating the single Basset integral atom: cB is the (constant)
    coefficient of that integral, and local(t,v) is the RHS with the integral set to
    zero. The kernel is verified to be the standard weakly-singular Basset form.

    Discretisation (same scheme as data_generator/integrate_basset.py, but the
    forces come from the spec, not a fixed model):
      * uniform time grid (memory scheme needs constant step h);
      * Basset integral via product-integration with weights
            w_k = sqrt(k) - sqrt(k-1),
        INT ~ (2/sqrt(h)) * sum_j (v_{j+1}-v_j) * w_{n-j};
      * implicit (backward) Euler in the local term, scalar root-find per step.
    """
    import re
    import sympy
    from scipy.optimize import brentq

    params = _params(spec)
    dep = spec["dependent_variable"]
    tv = _time_axis(spec)
    tname = tv["symbol"]
    lo, hi = tv["range"]
    n = int(spec.get("_n_total") or tv.get("n_points", 500))
    if n < 3:
        raise SystemExit("integrate_basset needs n_points >= 3")

    rhs = spec["rhs_for_integrator"]

    # The state appears both as a bare symbol (local force) and as v(tau) inside the
    # integral. Rename the history occurrence so the bare state stays a plain Symbol.
    rhs_renamed = re.sub(rf"\b{re.escape(dep)}\s*\(\s*tau\s*\)", "vhist(tau)", rhs)
    local_map = {nm: sympy.Symbol(nm)
                 for nm in (_declared_symbols(spec) | {tname, "tau"})}
    local_map["vhist"] = sympy.Function("vhist")
    expr = sympy.sympify(rhs_renamed, locals=local_map)

    integrals = list(expr.atoms(sympy.Integral))
    if len(integrals) != 1:
        raise SystemExit(f"expected exactly one memory integral, found "
                         f"{len(integrals)} — cannot treat as a Basset kernel")
    bint = integrals[0]

    # Verify the kernel is  d/dtau vhist(tau) / sqrt(t - tau)  integrated tau: 0->t.
    # Note: sympy stores 1/sqrt(x) as x**(-1/2), not a sqrt() node, so test the power.
    (dummy, t_lo, t_hi), = bint.limits
    weak_sing = (sympy.Symbol(tname) - sympy.Symbol("tau")) ** sympy.Rational(-1, 2)
    kernel_ok = (str(dummy) == "tau" and t_lo == 0 and str(t_hi) == tname
                 and bint.function.has(sympy.Derivative)
                 and bint.function.has(weak_sing))
    if not kernel_ok:
        raise SystemExit(f"integral is not a standard Basset kernel: {bint}")

    # Split: cB = coeff of the integral (must be constant in t and v); local = RHS|_{int=0}.
    B = sympy.Symbol("__BASSET__")
    expr_B = expr.xreplace({bint: B})
    cB_expr = sympy.diff(expr_B, B)
    local_expr = expr_B.subs(B, 0)

    subs = {sympy.Symbol(k): v for k, v in params.items()}
    cB_val = cB_expr.subs(subs)
    if cB_val.free_symbols:
        raise SystemExit(f"Basset coefficient is not constant after substituting "
                         f"params; residual symbols {cB_val.free_symbols}")
    cB = float(cB_val)

    f_local = sympy.lambdify([sympy.Symbol(tname), sympy.Symbol(dep)],
                             local_expr.subs(subs), modules="numpy")

    t = np.linspace(lo, hi, n)
    h = (hi - lo) / (n - 1)
    sqrt_h = np.sqrt(h)
    k = np.arange(0, n)
    sqrt_k = np.sqrt(k)
    w = np.empty(n)
    w[1:] = sqrt_k[1:] - sqrt_k[:-1]

    ic = spec.get("initial_conditions", {})
    v = np.zeros(n)
    v[0] = float(ic.get(dep, 0.0))
    dv = np.zeros(n)
    coef = cB * 2.0 / sqrt_h  # current-step Basset coefficient

    for nn in range(1, n):
        v_prev = v[nn - 1]
        tn = t[nn]
        if nn >= 2:
            j = np.arange(0, nn - 1)
            H_n = (2.0 / sqrt_h) * np.dot(dv[:nn - 1], w[nn - j])
        else:
            H_n = 0.0

        # dv/dt = local + cB*Basset, backward Euler:
        #   (vn - v_prev)/h = local(tn, vn) + coef*(vn - v_prev) + cB*H_n
        def R(vn):
            return ((vn - v_prev) / h
                    - float(f_local(tn, vn))
                    - coef * (vn - v_prev) - cB * H_n)

        lo_b, hi_b = v_prev - 1e-6, v_prev + 1e-6
        f_lo, f_hi = R(lo_b), R(hi_b)
        grow = 0
        while f_lo * f_hi > 0 and grow < 200:
            span = (hi_b - lo_b) * 2.0 + 1e-3
            lo_b -= span
            hi_b += span
            f_lo, f_hi = R(lo_b), R(hi_b)
            grow += 1
        if f_lo * f_hi > 0:
            raise SystemExit(f"root-find failed at step {nn} (params may diverge)")
        vn = brentq(R, lo_b, hi_b, xtol=1e-12, rtol=1e-12, maxiter=200)
        v[nn] = vn
        dv[nn - 1] = vn - v_prev

    cols = [tname, dep]
    data = [t, v]
    noise = float(spec.get("noise", 0.0) or 0.0)
    if noise > 0:
        data.append(_add_noise(v, noise, seed))
        cols.append(f"{dep}_noisy")
    return cols, np.column_stack(data)


_DISPATCH = {
    "evaluate_explicit": gen_evaluate_explicit,
    "root_solve_implicit": gen_root_solve_implicit,
    "integrate_ode": gen_integrate_ode,
    "integrate_system": gen_integrate_system,
    "integrate_dde": gen_integrate_dde,
    "integrate_basset": gen_integrate_basset,
}


# ============================================================
# Plotting (always emit a PNG next to the CSV)
# ============================================================

def _plot(cols: list[str], arr: np.ndarray, spec: dict, png_path: Path) -> None:
    """Render the generated data. The plot adapts to the integrator/shape:

      * 1 independent axis  -> dependent variable vs that axis (a curve).
      * 2 independent axes  -> a family of curves, one per value of the 2nd axis,
                               coloured by it (a small multiples / sweep view).
      * ODE system          -> every state variable vs time on one axis.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    integrator = spec.get("integrator", "")
    dep = spec.get("dependent_variable", cols[-1])
    ivs = _indep(spec)
    axis_names = [iv["symbol"] for iv in ivs]

    fig, ax = plt.subplots(figsize=(8, 4.5))

    # --- ODE system: plot each state column against time ---
    states = spec.get("state_variables", []) or []
    if integrator == "integrate_system" and states:
        t = arr[:, 0]
        for s in states:
            if s in cols:
                ax.plot(t, arr[:, cols.index(s)], lw=1.8, label=s)
        ax.set_xlabel(cols[0]); ax.set_ylabel("state"); ax.legend()

    # --- two independent axes ---
    elif len(axis_names) == 2 and dep in cols:
        x1, x2 = axis_names
        c1, c2, cy = cols.index(x1), cols.index(x2), cols.index(dep)
        vals2 = np.unique(arr[:, c2])
        gridded = len(vals2) <= max(40, int(np.sqrt(arr.shape[0]) * 2))
        if gridded:
            # regular grid: draw a family of curves, one per value of the 2nd axis
            cmap = plt.get_cmap("viridis")
            for j, v in enumerate(vals2):
                m = arr[:, c2] == v
                order = np.argsort(arr[m, c1])
                ax.plot(arr[m, c1][order], arr[m, cy][order], lw=1.3,
                        color=cmap(j / max(1, len(vals2) - 1)),
                        label=f"{x2}={v:.3g}" if len(vals2) <= 8 else None)
            ax.set_xlabel(x1); ax.set_ylabel(dep)
            if len(vals2) <= 8:
                ax.legend(fontsize=8, title=x2)
            else:
                sm = plt.cm.ScalarMappable(cmap=cmap,
                    norm=plt.Normalize(vals2.min(), vals2.max()))
                fig.colorbar(sm, ax=ax, label=x2)
        else:
            # randomly sampled box: scatter dep vs x1, coloured by x2
            sc = ax.scatter(arr[:, c1], arr[:, cy], c=arr[:, c2], s=8,
                            cmap="viridis", alpha=0.7)
            fig.colorbar(sc, ax=ax, label=x2)
            ax.set_xlabel(x1); ax.set_ylabel(dep)

    # --- three or more independent axes (random box): dep vs each axis, small multiples ---
    elif len(axis_names) >= 3 and dep in cols:
        plt.close(fig)
        m = len(axis_names)
        ncol = min(3, m)
        nrow = (m + ncol - 1) // ncol
        fig, axes = plt.subplots(nrow, ncol, figsize=(4.2 * ncol, 3.2 * nrow),
                                 squeeze=False)
        cy = cols.index(dep)
        for k, xn in enumerate(axis_names):
            a = axes[k // ncol][k % ncol]
            a.scatter(arr[:, cols.index(xn)], arr[:, cy], s=6, alpha=0.5)
            a.set_xlabel(xn); a.set_ylabel(dep); a.grid(alpha=0.3)
        for k in range(m, nrow * ncol):
            axes[k // ncol][k % ncol].axis("off")
        rid = spec.get("record_id", "")
        fig.suptitle(f"{rid}  [{spec.get('equation_type')} -> {integrator}]  "
                     f"({arr.shape[0]} pts, dep={dep} vs each of {m} vars)", fontsize=10)
        fig.tight_layout()
        fig.savefig(png_path, dpi=120)
        plt.close(fig)
        return

    # --- one independent axis (explicit / implicit / ode1): a single curve ---
    elif len(axis_names) >= 1 and dep in cols:
        x1 = axis_names[0]
        cx, cy = cols.index(x1), cols.index(dep)
        order = np.argsort(arr[:, cx])
        ax.plot(arr[:, cx][order], arr[:, cy][order], lw=1.8, label=dep)
        if f"{dep}_noisy" in cols:
            cn = cols.index(f"{dep}_noisy")
            ax.plot(arr[:, cx][order], arr[:, cn][order], ".", ms=3, alpha=0.4,
                    label=f"{dep}_noisy")
        ax.set_xlabel(x1); ax.set_ylabel(dep); ax.legend()

    else:  # fallback: dependent column vs row index
        cy = cols.index(dep) if dep in cols else arr.shape[1] - 1
        ax.plot(arr[:, cy], lw=1.5, label=dep)
        ax.set_xlabel("sample index"); ax.set_ylabel(dep); ax.legend()

    rid = spec.get("record_id", "")
    ax.set_title(f"{rid}  [{spec.get('equation_type')} -> {integrator}]", fontsize=10)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(png_path, dpi=120)
    plt.close(fig)


# ============================================================
# Sanity report (cheap numeric health check, for Stage 6c hand-off)
# ============================================================

def _health(cols: list[str], arr: np.ndarray, dep: str) -> dict:
    try:
        ycol = cols.index(dep)
    except ValueError:
        ycol = arr.shape[1] - 1
    y = arr[:, ycol]
    return {
        "n_points": int(arr.shape[0]),
        "n_columns": int(arr.shape[1]),
        "dep_min": float(np.min(y)),
        "dep_max": float(np.max(y)),
        "any_nan": bool(np.isnan(arr).any()),
        "any_inf": bool(np.isinf(arr).any()),
    }


# ============================================================
# Driver
# ============================================================

def generate(spec: dict, output_dir: Path, seed: int = 0,
             verbose: bool = True) -> dict:
    integrator = spec.get("integrator", "")
    gen = _DISPATCH.get(integrator)
    if gen is None:
        raise SystemExit(f"unknown integrator '{integrator}'. "
                         f"Known: {sorted(_DISPATCH)}")
    if integrator == "unsupported":
        raise SystemExit("spec is marked unsupported and cannot generate data")

    dep = spec.get("benchmark_output") or spec.get("dependent_variable", "y")
    cols, arr = gen(spec, seed)

    output_dir.mkdir(parents=True, exist_ok=True)
    rid = spec.get("record_id", "rec")
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    csv_path = output_dir / f"{rid}_gen{spec.get('generation','?')}_{ts}.csv"
    np.savetxt(csv_path, arr, delimiter=",", header=",".join(cols), comments="")

    png_path = csv_path.with_suffix(".png")
    try:
        _plot(cols, arr, spec, png_path)
        plotted = True
    except Exception as e:
        plotted = False
        print(f"    plot       : FAILED ({type(e).__name__}: {e})", file=sys.stderr)

    health = _health(cols, arr, dep)
    if verbose:
        print(f"    integrator : {integrator}", file=sys.stderr)
        print(f"    columns    : {cols}", file=sys.stderr)
        print(f"    points     : {health['n_points']}", file=sys.stderr)
        print(f"    {dep} range : [{health['dep_min']:.4g}, {health['dep_max']:.4g}]",
              file=sys.stderr)
        flags = []
        if health["any_nan"]:
            flags.append("NaN")
        if health["any_inf"]:
            flags.append("Inf")
        print(f"    health     : {'OK' if not flags else 'BAD: ' + ','.join(flags)}",
              file=sys.stderr)
        print(f"    wrote      : {csv_path}", file=sys.stderr)
        if plotted:
            print(f"    plot       : {png_path}", file=sys.stderr)
    return {"csv_path": str(csv_path),
            "png_path": str(png_path) if plotted else None,
            "columns": cols, "health": health}


def _load_specs(path: Path) -> list[dict]:
    if path.suffix == ".jsonl":
        return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()
                if l.strip()]
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, list) else [data]


def main() -> None:
    p = argparse.ArgumentParser(
        description="Stage 6b: generate data points from a DataGenSpec (pure scipy).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--spec", required=True, help="DataGenSpec .jsonl or .json")
    p.add_argument("--index", type=int, default=None,
                   help="only this spec index in the file (default: all)")
    p.add_argument("--output-dir", default=None,
                   help="default: outputs/data/")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--n-total", type=int, default=None,
                   help="target total number of data points per equation. Multi-var "
                        "explicit/implicit -> random box sampling; single-var / ODE -> "
                        "that many samples along the axis. Default: use spec n_points.")
    args = p.parse_args()

    spec_path = Path(args.spec)
    if not spec_path.exists():
        raise SystemExit(f"spec not found: {spec_path}")
    specs = _load_specs(spec_path)
    specs = [s for s in specs if "error" not in s]
    if args.index is not None:
        specs = [specs[args.index]]
    if not specs:
        raise SystemExit("no valid specs to generate from")

    out_dir = Path(args.output_dir) if args.output_dir else (
        Path(__file__).resolve().parents[1] / "outputs" / "data")
    failure_path = out_dir / "generation_failures.jsonl"

    for i, spec in enumerate(specs, 1):
        if args.n_total:
            spec["_n_total"] = args.n_total
        rid = spec.get("record_id", f"rec{i}")
        print(f"\n[{i}/{len(specs)}] {rid} "
              f"({spec.get('equation_type')} -> {spec.get('integrator')})",
              file=sys.stderr)
        try:
            generate(spec, out_dir, seed=args.seed)
        except Exception as e:
            failure = {
                "record_id": rid,
                "generation": spec.get("generation"),
                "equation_type": spec.get("equation_type"),
                "integrator": spec.get("integrator"),
                "error": f"{type(e).__name__}: {e}",
            }
            out_dir.mkdir(parents=True, exist_ok=True)
            with failure_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(failure, ensure_ascii=False) + "\n")
            print(f"    FAILED: {failure['error']}", file=sys.stderr)


if __name__ == "__main__":
    main()
