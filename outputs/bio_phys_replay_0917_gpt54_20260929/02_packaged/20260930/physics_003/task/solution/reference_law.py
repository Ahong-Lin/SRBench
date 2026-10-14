"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['rho', 'T', 'B2', 'B3']
TARGET = 'P'
PARAMETERS = {'alpha2': 0.4, 'beta3': 0.5, 'gamma3': 0.15, 'alpha23': 0.5}
_symbols = {name: sympy.Symbol(name) for name in ['rho', 'T', 'B2', 'B3', 'alpha2', 'beta3', 'gamma3', 'alpha23', 'P']}
_expression = sympy.sympify('rho*T*(1 + (B2/(1 + alpha2*T))*rho + (B3/(1 + beta3*T + gamma3*T**2 + alpha23*B2*rho))*rho**2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
