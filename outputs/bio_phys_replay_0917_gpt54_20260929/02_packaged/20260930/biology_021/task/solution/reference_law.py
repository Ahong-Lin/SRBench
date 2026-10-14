"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'Z', 'A', 'C', 'inactivation_capacity']
TARGET = 'dA_dt'
PARAMETERS = {'k_activation': 0.02, 'k_unbinding': 0.15, 'k_cleave': 0.8, 'k_inactivation': 0.2, 'k_capacity_depletion': 0.03, 'cooperativity_inactivation': 1.5}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'Z', 'A', 'C', 'inactivation_capacity', 'k_activation', 'k_unbinding', 'k_cleave', 'k_inactivation', 'k_capacity_depletion', 'cooperativity_inactivation', 'dA_dt']}
_expression = sympy.sympify('k_cleave * C - k_inactivation * A / (1 + (inactivation_capacity * A)**cooperativity_inactivation)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
