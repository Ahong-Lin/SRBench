"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['p_f', 'p_m', 'env']
TARGET = 'G_het'
PARAMETERS = {'env_sel': 0.35, 'mismatch_sens': 1.5, 'crowding_curv': 2.0, 'stress_window_curv': 3.0}
_symbols = {name: sympy.Symbol(name) for name in ['p_f', 'p_m', 'env', 'env_sel', 'mismatch_sens', 'crowding_curv', 'stress_window_curv', 'G_het']}
_expression = sympy.sympify('(p_f*(1 - p_m) + (1 - p_f)*p_m) + env_sel*tanh(env*(1 + mismatch_sens*Abs(p_f - p_m)))*exp(-stress_window_curv*(env*(1 + mismatch_sens*Abs(p_f - p_m)))**2)*(p_f*(1 - p_m) + (1 - p_f)*p_m)*(1 - (p_f*(1 - p_m) + (1 - p_f)*p_m))/(1 + crowding_curv*(p_f*(1 - p_m) + (1 - p_f)*p_m))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
