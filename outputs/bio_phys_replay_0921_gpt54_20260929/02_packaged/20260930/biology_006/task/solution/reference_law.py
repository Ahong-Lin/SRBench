"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'x', 'u', 'replenishment_fatigue', 'release_site_occupancy']
TARGET = 'dx_dt'
PARAMETERS = {'recovery_time_constant': 0.8, 'facilitation_time_constant': 0.2, 'presynaptic_rate': 15.0, 'baseline_utilization': 0.25, 'fatigue_build_time_constant': 0.5, 'fatigue_recovery_time_constant': 1.2, 'release_site_reset_time_constant': 0.05}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'x', 'u', 'replenishment_fatigue', 'release_site_occupancy', 'recovery_time_constant', 'facilitation_time_constant', 'presynaptic_rate', 'baseline_utilization', 'fatigue_build_time_constant', 'fatigue_recovery_time_constant', 'release_site_reset_time_constant', 'dx_dt']}
_expression = sympy.sympify('(1 - x)/(recovery_time_constant*(1 + replenishment_fatigue)) - presynaptic_rate*(1 - release_site_occupancy)*u*x**2/((1 + replenishment_fatigue)*(1 + baseline_utilization*replenishment_fatigue))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
