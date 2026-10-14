"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['c', 'i', 's', 'q']
TARGET = 'new_infection_rate'
PARAMETERS = {'exposure_half_saturation': 0.15, 'susceptible_saturation_modulation': 3.0, 'susceptible_curvature_modulation': 1.2, 'infectious_threshold_modulation': 2.0, 'infectious_curvature_modulation': 1.0, 'infectious_redundancy_shape': 1.5}
_symbols = {name: sympy.Symbol(name) for name in ['c', 'i', 's', 'q', 'exposure_half_saturation', 'susceptible_saturation_modulation', 'susceptible_curvature_modulation', 'infectious_threshold_modulation', 'infectious_curvature_modulation', 'infectious_redundancy_shape', 'new_infection_rate']}
_expression = sympy.sympify('s*c*(q*i)**(1 + susceptible_curvature_modulation*s + infectious_curvature_modulation*i)/(exposure_half_saturation/((1 + susceptible_saturation_modulation*s)*(1 + infectious_threshold_modulation*i)) + (q*i)**(1 + susceptible_curvature_modulation*s + infectious_curvature_modulation*i))*(1 + infectious_redundancy_shape*i/(1 + q*i))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
