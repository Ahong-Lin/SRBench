"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'p', 'q']
TARGET = 'dp_dt'
PARAMETERS = {'selection_coefficient': 0.8, 'frequency_dependence_strength': 2.0, 'feedback_relaxation_rate': 0.7, 'feedback_build_rate': 0.8, 'frequency_dependence_steepening': 4.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'p', 'q', 'selection_coefficient', 'frequency_dependence_strength', 'feedback_relaxation_rate', 'feedback_build_rate', 'frequency_dependence_steepening', 'dp_dt']}
_expression = sympy.sympify('selection_coefficient*p*(1 - p)/(1 + q*p**2 + frequency_dependence_strength*q*p + frequency_dependence_steepening*q*p**3)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
