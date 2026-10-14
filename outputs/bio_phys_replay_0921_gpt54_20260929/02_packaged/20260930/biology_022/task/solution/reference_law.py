"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['S', 'I', 'E_total', 'k_cat']
TARGET = 'v_instantaneous'
PARAMETERS = {'K_m': 1.5, 'K_i': 1.0, 'inhibitor_nonlinearity': 0.6, 'substrate_self_inhibition': 0.25, 'crowding_inhibitor_coupling': 1.5}
_symbols = {name: sympy.Symbol(name) for name in ['S', 'I', 'E_total', 'k_cat', 'K_m', 'K_i', 'inhibitor_nonlinearity', 'substrate_self_inhibition', 'crowding_inhibitor_coupling', 'v_instantaneous']}
_expression = sympy.sympify('k_cat*E_total*S/(K_m*(1 + I/K_i + inhibitor_nonlinearity*(I/K_i)**2) + S + substrate_self_inhibition*(1 + crowding_inhibitor_coupling*(I/K_i)/(1 + I/K_i))**2*S**2/K_m)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
