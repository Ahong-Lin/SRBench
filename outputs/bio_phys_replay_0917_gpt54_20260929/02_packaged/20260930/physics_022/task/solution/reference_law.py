"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['Q', 'r', 'epsilon', 'a']
TARGET = 'E'
PARAMETERS = {'E_sat': 100000.0}
_symbols = {name: sympy.Symbol(name) for name in ['Q', 'r', 'epsilon', 'a', 'E_sat', 'E']}
_expression = sympy.sympify('Q/(4*pi*epsilon*r**2) + Q*a/(4*pi*epsilon*r**3*(1 - a/r + a/(epsilon*r))*(1 + Q/(4*pi*epsilon*E_sat*a**2) + (Q/(4*pi*epsilon*E_sat*a**2))**2))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
