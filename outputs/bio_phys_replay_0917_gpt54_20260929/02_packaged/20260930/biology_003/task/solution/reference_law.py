"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'L', 'M', 'P', 'C']
TARGET = 'dC_dt'
PARAMETERS = {'progression_rate': 0.35, 'presymptomatic_progression_rate': 0.7, 'clearance_rate': 0.2, 'maturation_heterogeneity': 0.01, 'contagious_feedback': 0.01, 'contagious_clearance_burden': 0.03}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'L', 'M', 'P', 'C', 'progression_rate', 'presymptomatic_progression_rate', 'clearance_rate', 'maturation_heterogeneity', 'contagious_feedback', 'contagious_clearance_burden', 'dC_dt']}
_expression = sympy.sympify('presymptomatic_progression_rate*P/(1 + contagious_feedback*C) - clearance_rate*C*(1 + contagious_clearance_burden*C)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
