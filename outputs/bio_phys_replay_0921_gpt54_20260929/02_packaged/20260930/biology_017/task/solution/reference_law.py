"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'R', 'C', 'J']
TARGET = 'dC_dt'
PARAMETERS = {'resource_growth_rate': 0.45, 'encounter_rate': 0.018, 'conversion_efficiency': 0.55, 'consumer_mortality_rate': 0.12, 'handling_saturation_scale': 0.03, 'consumer_interference_scale': 0.025, 'juvenile_maturation_rate': 0.35, 'juvenile_mortality_rate': 0.08, 'high_resource_inhibition_scale': 0.004}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'R', 'C', 'J', 'resource_growth_rate', 'encounter_rate', 'conversion_efficiency', 'consumer_mortality_rate', 'handling_saturation_scale', 'consumer_interference_scale', 'juvenile_maturation_rate', 'juvenile_mortality_rate', 'high_resource_inhibition_scale', 'dC_dt']}
_expression = sympy.sympify('juvenile_maturation_rate * R / (1 + handling_saturation_scale * R) * exp(-high_resource_inhibition_scale * R) * J - consumer_mortality_rate * C', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
