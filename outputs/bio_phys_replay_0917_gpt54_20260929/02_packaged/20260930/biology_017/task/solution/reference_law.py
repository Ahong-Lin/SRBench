"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['S', 'K_I', 'H', 'K_H_app']
TARGET = 'v0'
PARAMETERS = {'k_cat': 8.0, 'E_total': 0.1, 'K_M': 40.0, 'K_H': 1.0, 'n_H': 2.0}
_symbols = {name: sympy.Symbol(name) for name in ['S', 'K_I', 'H', 'K_H_app', 'k_cat', 'E_total', 'K_M', 'K_H', 'n_H', 'v0']}
_expression = sympy.sympify('E_total*K_H_app*K_I*S*k_cat/(((H/K_H)**n_H + 1)*(H*K_I*K_M + K_H_app*K_I*K_M + K_H_app*K_I*S + K_H_app*S**2))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
