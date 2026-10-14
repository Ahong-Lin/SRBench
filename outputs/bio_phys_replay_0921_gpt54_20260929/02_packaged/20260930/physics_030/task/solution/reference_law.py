"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'eta', 'u', 'q', 'stiffness_overshoot_state']
TARGET = 'deta_dt'
PARAMETERS = {'gravity_acceleration': 9.81, 'mode_wavenumber': 1.5, 'fluid_depth': 1.2, 'nonlinear_restoring_coefficient': 2.5, 'stiffness_relaxation_time': 0.35}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'eta', 'u', 'q', 'stiffness_overshoot_state', 'gravity_acceleration', 'mode_wavenumber', 'fluid_depth', 'nonlinear_restoring_coefficient', 'stiffness_relaxation_time', 'deta_dt']}
_expression = sympy.sympify('u/(1 + nonlinear_restoring_coefficient*eta**2*(q + stiffness_overshoot_state**2))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
