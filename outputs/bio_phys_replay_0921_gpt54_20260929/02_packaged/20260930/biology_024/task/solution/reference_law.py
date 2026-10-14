"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'S', 'P', 'K_i', 'I_slow']
TARGET = 'dP_dt'
PARAMETERS = {'V_max': 12.0, 'K_m': 20.0, 'k_Ki_decay': 0.12, 'K_i_min': 2.5, 'K_icat': 40.0, 'k_Islow_relax': 0.18, 'K_P_sat': 35.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'S', 'P', 'K_i', 'I_slow', 'V_max', 'K_m', 'k_Ki_decay', 'K_i_min', 'K_icat', 'k_Islow_relax', 'K_P_sat', 'dP_dt']}
_expression = sympy.sympify('V_max*S/((1 + I_slow/K_icat)*(K_m*(1 + P/K_i) + S))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
