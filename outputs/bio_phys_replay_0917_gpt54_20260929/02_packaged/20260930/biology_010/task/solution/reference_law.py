"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['mu', 's', 'h', 'nu']
TARGET = 'q_star'
PARAMETERS = {'F': 0.2}
_symbols = {name: sympy.Symbol(name) for name in ['mu', 's', 'h', 'nu', 'F', 'q_star']}
_expression = sympy.sympify('(-h*(1 - F) + sqrt((h*(1 - F))**2 + 4*(mu*mu/(mu + nu))/((s/(1 + s))*(F + (1 - F)))))/2', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
