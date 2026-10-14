"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'U', 'R', 'Q', 'H']
TARGET = 'dU_dt'
PARAMETERS = {'pressure_gradient_magnitude': 120.0, 'fluid_density': 1000.0, 'viscous_drag_rate': 0.8, 'nonlinear_drag_coefficient': 1.8, 'resistance_relaxation_rate': 1.2, 'drag_saturation_velocity': 0.12, 'slow_resistance_relaxation_rate': 0.18, 'slow_resistance_weight': 0.6, 'startup_phase_relaxation_rate': 0.5, 'startup_phase_coupling': 0.8}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'U', 'R', 'Q', 'H', 'pressure_gradient_magnitude', 'fluid_density', 'viscous_drag_rate', 'nonlinear_drag_coefficient', 'resistance_relaxation_rate', 'drag_saturation_velocity', 'slow_resistance_relaxation_rate', 'slow_resistance_weight', 'startup_phase_relaxation_rate', 'startup_phase_coupling', 'dU_dt']}
_expression = sympy.sympify('pressure_gradient_magnitude / fluid_density - viscous_drag_rate * (R + slow_resistance_weight*Q) * U', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
