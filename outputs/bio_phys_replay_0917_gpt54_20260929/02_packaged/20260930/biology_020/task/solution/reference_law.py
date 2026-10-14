"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'S', 'C', 'P', 'EP']
TARGET = 'dP_dt'
PARAMETERS = {'E_total': 1.0, 'k_on': 0.08, 'k_off': 1.2, 'k_cat': 2.0, 'k_on_P': 0.05, 'k_off_P': 0.2, 'K_I_P': 30.0, 'K_I_cat': 40.0, 'n_I_cat': 2.0, 'K_S_protect': 50.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'S', 'C', 'P', 'EP', 'E_total', 'k_on', 'k_off', 'k_cat', 'k_on_P', 'k_off_P', 'K_I_P', 'K_I_cat', 'n_I_cat', 'K_S_protect', 'dP_dt']}
_expression = sympy.sympify('k_cat*C/(1 + (P/(K_I_cat*(1 + S/K_S_protect)))**n_I_cat) - k_on_P*(E_total - C - EP)*P/(1 + P/K_I_P) + k_off_P*EP', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
