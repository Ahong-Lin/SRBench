"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['sqrt_s', 'M', 'Gamma', 'C']
TARGET = 'sigma_res'
PARAMETERS = {'alpha': 0.5, 'Lambda_C': 0.3, 'Delta_disp': 0.03, 'Lambda_disp': 0.35}
_symbols = {name: sympy.Symbol(name) for name in ['sqrt_s', 'M', 'Gamma', 'C', 'alpha', 'Lambda_C', 'Delta_disp', 'Lambda_disp', 'sigma_res']}
_expression = sympy.sympify('C*M**2*(Gamma*sqrt_s/M)**2*(1 + alpha*(log(1 + exp((sqrt_s**2 - M**2)/Lambda_C**2)) - log(2)))*((1 + tanh((sqrt_s**2 - M**2)/Lambda_C**2))/2)/(((sqrt_s**2 - M**2) - Delta_disp*tanh((sqrt_s**2 - M**2)/Lambda_disp**2))**2 + M**2*(Gamma*sqrt_s/M)**2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
