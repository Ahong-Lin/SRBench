"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'p', 'extinction_rate']
TARGET = 'dp_dt'
PARAMETERS = {'colonization_rate': 1.2, 'colonization_density_dependence': 0.8, 'colonization_saturation_scale': 2.0, 'extinction_relaxation_rate': 0.8, 'extinction_occupancy_sensitivity': 0.9, 'extinction_feedback_half_saturation': 0.3, 'colonization_stress_sensitivity': 3.0, 'colonization_stress_half_saturation': 5.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'p', 'extinction_rate', 'colonization_rate', 'colonization_density_dependence', 'colonization_saturation_scale', 'extinction_relaxation_rate', 'extinction_occupancy_sensitivity', 'extinction_feedback_half_saturation', 'colonization_stress_sensitivity', 'colonization_stress_half_saturation', 'dp_dt']}
_expression = sympy.sympify('colonization_rate*p*(1 - p)*(1 + colonization_density_dependence*p/(1 + colonization_saturation_scale*p))*exp(-colonization_stress_sensitivity*extinction_rate/(1 + colonization_stress_half_saturation*extinction_rate)) - extinction_rate*p', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
