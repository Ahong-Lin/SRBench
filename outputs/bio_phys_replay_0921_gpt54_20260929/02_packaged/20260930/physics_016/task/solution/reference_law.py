"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['T', 'Delta']
TARGET = 'sigma'
PARAMETERS = {'sigma0': 1.0, 'k_B': 0.08617, 'T_dis': 120.0, 'beta_shape': 2.0, 'gamma_cross': 1.5, 'eta_barrier': 3.0, 'Delta_filter': 60.0}
_symbols = {name: sympy.Symbol(name) for name in ['T', 'Delta', 'sigma0', 'k_B', 'T_dis', 'beta_shape', 'gamma_cross', 'eta_barrier', 'Delta_filter', 'sigma']}
_expression = sympy.sympify('sigma0*exp(-Delta/(k_B*(T + T_dis*(Delta/(Delta + k_B*T))**2/(((1 + beta_shape*(k_B*T/Delta))*(1 + gamma_cross*(k_B*T/Delta)/(1 + k_B*T/Delta)))*(1 + eta_barrier*Delta/(Delta + Delta_filter))))))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
