"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['F', 'm', 'g']
TARGET = 'a'
PARAMETERS = {'mu_s': 0.35, 'mu_k': 0.25, 'beta': 2.0, 'gamma': 3.0, 'eta': 0.08, 'N0': 10.0, 'delta': 0.5}
_symbols = {name: sympy.Symbol(name) for name in ['F', 'm', 'g', 'mu_s', 'mu_k', 'beta', 'gamma', 'eta', 'N0', 'delta', 'a']}
_expression = sympy.sympify('Piecewise((0, Abs(F) <= (mu_s + eta*log(1 + m*g/N0))*m*g), ((F - mu_k*m*g*sign(F)/(1 + beta*(1 - exp(-gamma*(1 + delta*log(1 + m*g/N0))*(Abs(F)/(m*g) - (mu_s + eta*log(1 + m*g/N0)))))))/m, True))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
