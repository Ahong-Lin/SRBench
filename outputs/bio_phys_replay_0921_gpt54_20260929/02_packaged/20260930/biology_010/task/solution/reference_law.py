"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'C', 'H', 'B']
TARGET = 'dC_dt'
PARAMETERS = {'stimulus_strength': 1.2, 'k_release': 0.9, 'k_extrusion': 0.7, 'k_sensor_activation': 0.9, 'k_sensor_relaxation': 0.25, 'pump_saturation_scale': 1.0, 'release_inactivation_scale': 0.8, 'k_buffer_bind': 0.8, 'k_buffer_unbind': 0.18, 'buffer_binding_scale': 0.6, 'k_cicr_release': 1.3, 'sensor_activation_scale': 1.5}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'C', 'H', 'B', 'stimulus_strength', 'k_release', 'k_extrusion', 'k_sensor_activation', 'k_sensor_relaxation', 'pump_saturation_scale', 'release_inactivation_scale', 'k_buffer_bind', 'k_buffer_unbind', 'buffer_binding_scale', 'k_cicr_release', 'sensor_activation_scale', 'dC_dt']}
_expression = sympy.sympify('(k_release*stimulus_strength*(1 - H))/(1 + release_inactivation_scale*C) + (k_cicr_release*stimulus_strength*C*(1 - H))/(1 + release_inactivation_scale*C) - (k_extrusion*C)/(1 + pump_saturation_scale*C) - (k_buffer_bind*C*(1 - B))/(1 + buffer_binding_scale*C) + k_buffer_unbind*B', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
