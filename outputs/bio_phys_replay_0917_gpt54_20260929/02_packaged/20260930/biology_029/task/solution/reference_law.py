"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['p', 'c0', 'p_trigger', 'rho']
TARGET = 'c_eff'
PARAMETERS = {}
_symbols = {name: sympy.Symbol(name) for name in ['p', 'c0', 'p_trigger', 'rho', 'c_eff']}
_expression = sympy.sympify('c0*(1 - (rho/(1 + rho))*(1 - exp(-(((p - p_trigger)/(p_trigger + p_trigger**2))*((1 + tanh((p - p_trigger)/p_trigger))/2))/(1 + ((p - p_trigger)/(p_trigger + p_trigger**2))*((1 + tanh((p - p_trigger)/p_trigger))/2))))*((1 + tanh((p - p_trigger)/p_trigger))/2))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
