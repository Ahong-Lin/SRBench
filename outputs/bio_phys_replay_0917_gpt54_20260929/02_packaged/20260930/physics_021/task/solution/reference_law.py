"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'k', 'epsilon', 'q', 'r']
TARGET = 'dk_dt'
PARAMETERS = {'C_epsilon2': 1.9, 'C_cascade': 0.7, 'tau_cascade': 1.5, 'tau_transfer': 3.0, 'C_transfer': 0.8, 'q_saturation': 1.0, 'k_feed_scale': 0.8, 'k_shutdown_scale': 0.2}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'k', 'epsilon', 'q', 'r', 'C_epsilon2', 'C_cascade', 'tau_cascade', 'tau_transfer', 'C_transfer', 'q_saturation', 'k_feed_scale', 'k_shutdown_scale', 'dk_dt']}
_expression = sympy.sympify('-epsilon', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
