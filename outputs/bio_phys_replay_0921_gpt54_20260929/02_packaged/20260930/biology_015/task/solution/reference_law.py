"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'E', 'I', 'progression_rate', 'infectious_maturation']
TARGET = 'dI_dt'
PARAMETERS = {'removal_rate': 0.6, 'progression_relaxation_rate': 0.8, 'progression_feedback_scale': 0.25, 'infectious_maturation_rate': 1.2}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'E', 'I', 'progression_rate', 'infectious_maturation', 'removal_rate', 'progression_relaxation_rate', 'progression_feedback_scale', 'infectious_maturation_rate', 'dI_dt']}
_expression = sympy.sympify('progression_rate*E - removal_rate*(1 + (infectious_maturation**2/(1 + infectious_maturation**2))*(1 - E/(E + progression_feedback_scale)))*I', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
