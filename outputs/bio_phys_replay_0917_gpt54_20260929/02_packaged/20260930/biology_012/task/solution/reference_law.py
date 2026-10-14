"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['p', 'N', 'D', 'C']
TARGET = 'V_delta_p'
PARAMETERS = {}
_symbols = {name: sympy.Symbol(name) for name in ['p', 'N', 'D', 'C', 'V_delta_p']}
_expression = sympy.sympify('p*(1 - p)*(1 + D*(1 + (C*(4*p*(1 - p))**4)/(1 + C*(4*p*(1 - p))**4)))/(2*N)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
