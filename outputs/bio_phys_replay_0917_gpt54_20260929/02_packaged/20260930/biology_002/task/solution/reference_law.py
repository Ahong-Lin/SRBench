"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'S', 'I', 'R', 'beta']
TARGET = 'dI_dt'
PARAMETERS = {'gamma': 0.2, 'alpha': 20.0, 'kappa': 0.08, 'beta_floor': 0.35}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'S', 'I', 'R', 'beta', 'gamma', 'alpha', 'kappa', 'beta_floor', 'dI_dt']}
_expression = sympy.sympify('beta*S*I/((S + I + R)*(1 + alpha*I/(S + I + R))) - gamma*I*(1 + alpha*I/((S + I + R) + alpha*I + alpha**2*I**2/(S + I + R)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
