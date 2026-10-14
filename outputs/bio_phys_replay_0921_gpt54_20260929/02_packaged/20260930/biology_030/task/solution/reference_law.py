"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'P', 'S', 'R', 'B']
TARGET = 'dP_dt'
PARAMETERS = {'cardiac_delivery_baseline': 0.9, 'cardiac_delivery_gain': 3.0, 'peripheral_resistance_baseline': 0.8, 'peripheral_resistance_gain': 1.6, 'arterial_compliance': 2.0, 'pressure_setpoint': 95.0, 'baroreflex_pressure_scale': 12.0, 'autonomic_time_constant': 8.0, 'vascular_saturation_scale': 0.7, 'vascular_time_constant': 20.0, 'cardiac_afterload_pressure_scale': 120.0, 'baroreflex_resetting_gain': 0.25, 'baroreflex_resetting_time_constant': 120.0, 'baroreflex_asymmetry_gain': 0.35}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'P', 'S', 'R', 'B', 'cardiac_delivery_baseline', 'cardiac_delivery_gain', 'peripheral_resistance_baseline', 'peripheral_resistance_gain', 'arterial_compliance', 'pressure_setpoint', 'baroreflex_pressure_scale', 'autonomic_time_constant', 'vascular_saturation_scale', 'vascular_time_constant', 'cardiac_afterload_pressure_scale', 'baroreflex_resetting_gain', 'baroreflex_resetting_time_constant', 'baroreflex_asymmetry_gain', 'dP_dt']}
_expression = sympy.sympify('(cardiac_delivery_baseline + cardiac_delivery_gain*S*exp(-P/cardiac_afterload_pressure_scale) - P/(peripheral_resistance_baseline + peripheral_resistance_gain*R))/arterial_compliance', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
