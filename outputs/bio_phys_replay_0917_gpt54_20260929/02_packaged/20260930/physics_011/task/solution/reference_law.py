"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'v', 'wake_drag', 'regime_occupancy', 'local_flow_velocity']
TARGET = 'dv_dt'
PARAMETERS = {'g': 9.81, 'drag_coefficient': 0.2, 'mass': 1.0, 'wake_relaxation_time': 0.8, 'regime_relaxation_time': 1.2, 'critical_speed': 8.0, 'drag_reduction_fraction': 0.5, 'drag_shape_fraction': 0.8, 'flow_relaxation_time': 1.5, 'entrainment_fraction': 0.35}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'v', 'wake_drag', 'regime_occupancy', 'local_flow_velocity', 'g', 'drag_coefficient', 'mass', 'wake_relaxation_time', 'regime_relaxation_time', 'critical_speed', 'drag_reduction_fraction', 'drag_shape_fraction', 'flow_relaxation_time', 'entrainment_fraction', 'dv_dt']}
_expression = sympy.sympify('-g - (wake_drag * regime_occupancy / mass) * (v - local_flow_velocity) * Abs(v - local_flow_velocity) * (1 + drag_shape_fraction * Abs(v - local_flow_velocity) / (critical_speed + Abs(v - local_flow_velocity)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
