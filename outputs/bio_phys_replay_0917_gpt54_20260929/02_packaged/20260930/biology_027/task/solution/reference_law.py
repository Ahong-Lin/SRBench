"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'S', 'I', 'R', 'C']
TARGET = 'dI_dt'
PARAMETERS = {'beta': 1.2, 'gamma': 0.25, 'kappa': 0.4, 'rho': 0.08, 'alpha_sus': 4.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'S', 'I', 'R', 'C', 'beta', 'gamma', 'kappa', 'rho', 'alpha_sus', 'dI_dt']}
_expression = sympy.sympify('beta*C*S*I/((S + I + R)*(1 + alpha_sus*(1 - S/(S + I + R))*(1 + R/(S + I + R + alpha_sus)))) - gamma*I - kappa*R*S*I/((S + I + R)*(S + I + R + R))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
