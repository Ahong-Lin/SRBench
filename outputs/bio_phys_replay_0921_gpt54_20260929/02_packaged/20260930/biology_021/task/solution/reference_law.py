"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['L', 'Kd', 'crowding_level']
TARGET = 'theta_bound'
PARAMETERS = {'heterogeneity_width': 1.2, 'environment_modulation': 0.35, 'skew_coupling': 1.6, 'affinity_shift_coupling': 2.0, 'shift_saturation_strength': 2.5}
_symbols = {name: sympy.Symbol(name) for name in ['L', 'Kd', 'crowding_level', 'heterogeneity_width', 'environment_modulation', 'skew_coupling', 'affinity_shift_coupling', 'shift_saturation_strength', 'theta_bound']}
_expression = sympy.sympify('L/(L + Kd*exp(-affinity_shift_coupling*crowding_level/((1 + heterogeneity_width*(1 + environment_modulation*crowding_level))*(1 + shift_saturation_strength*heterogeneity_width*(1 + environment_modulation*crowding_level))))*sqrt(1 + heterogeneity_width*(1 + environment_modulation*crowding_level)*L/(Kd*exp(-affinity_shift_coupling*crowding_level/((1 + heterogeneity_width*(1 + environment_modulation*crowding_level))*(1 + shift_saturation_strength*heterogeneity_width*(1 + environment_modulation*crowding_level))))) + skew_coupling*(heterogeneity_width*(1 + environment_modulation*crowding_level)*L/(Kd*exp(-affinity_shift_coupling*crowding_level/((1 + heterogeneity_width*(1 + environment_modulation*crowding_level))*(1 + shift_saturation_strength*heterogeneity_width*(1 + environment_modulation*crowding_level))))))**2/(1 + L/(Kd*exp(-affinity_shift_coupling*crowding_level/((1 + heterogeneity_width*(1 + environment_modulation*crowding_level))*(1 + shift_saturation_strength*heterogeneity_width*(1 + environment_modulation*crowding_level))))))))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
