"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['D', 'tau', 'q', 'gamma_spread']
TARGET = 'p_inf'
PARAMETERS = {'beta_inf': 0.18, 'kappa_inf': 2.0, 'gamma_adapt': 0.08, 'gamma_crowd': 1.0, 'gamma_hard': 2.5}
_symbols = {name: sympy.Symbol(name) for name in ['D', 'tau', 'q', 'gamma_spread', 'beta_inf', 'kappa_inf', 'gamma_adapt', 'gamma_crowd', 'gamma_hard', 'p_inf']}
_expression = sympy.sympify('1 - (1 + beta_inf*q*((1 + gamma_spread*((1 + gamma_adapt*D*tau/(1 + gamma_crowd*gamma_adapt*D))**gamma_hard - 1))**(1/gamma_spread) - 1)*D/(gamma_adapt*D*kappa_inf))**(-kappa_inf)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
