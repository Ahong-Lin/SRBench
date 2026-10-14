"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'H', 'P', 'A']
TARGET = 'dH_dt'
PARAMETERS = {'prey_growth_rate': 0.8, 'capture_rate': 1.2, 'conversion_efficiency': 0.18, 'consumer_mortality_rate': 0.25, 'half_saturation_prey': 40.0, 'consumer_interference_rate': 1.5, 'prey_carrying_capacity': 300.0, 'activity_relaxation_rate': 0.6, 'activity_half_saturation_prey': 35.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'H', 'P', 'A', 'prey_growth_rate', 'capture_rate', 'conversion_efficiency', 'consumer_mortality_rate', 'half_saturation_prey', 'consumer_interference_rate', 'prey_carrying_capacity', 'activity_relaxation_rate', 'activity_half_saturation_prey', 'dH_dt']}
_expression = sympy.sympify('prey_growth_rate*H*(1 - H/prey_carrying_capacity) - capture_rate*H**2*A/((half_saturation_prey + H + consumer_interference_rate*A)*(half_saturation_prey + H))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
