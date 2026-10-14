"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['q', 'r', 'epsilon_0', 'd']
TARGET = 'E'
PARAMETERS = {'a': 0.01, 'beta': 1.0, 'gamma': 1.2}
_symbols = {name: sympy.Symbol(name) for name in ['q', 'r', 'epsilon_0', 'd', 'a', 'beta', 'gamma', 'E']}
_expression = sympy.sympify('q/(4*pi*epsilon_0)*(r/(r**2 + a**2*(1 + beta*(1 - exp(-r/a))*(1 + gamma*exp(-r/a))))**(3/2) - (2*d - r)/((2*d - r)**2 + a**2*(1 + beta*(1 - exp(-(2*d - r)/a))*(1 + gamma*exp(-(2*d - r)/a))))**(3/2))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
