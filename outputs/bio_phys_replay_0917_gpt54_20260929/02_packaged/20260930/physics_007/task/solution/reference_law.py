"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['kappa', 'eta', 'zeta', 'chi']
TARGET = 'Omega'
PARAMETERS = {}
_symbols = {name: sympy.Symbol(name) for name in ['kappa', 'eta', 'zeta', 'chi', 'Omega']}
_expression = sympy.sympify('Abs(sin(kappa/2))*sqrt(1 + eta*(sin(kappa/2)**2/(1 + zeta*eta*sin(kappa/2)**2) + chi*sin(kappa)**2/(1 + zeta*eta*chi*sin(kappa)**2)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
