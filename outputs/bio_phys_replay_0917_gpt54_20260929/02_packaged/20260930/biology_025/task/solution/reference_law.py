"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['G', 'E']
TARGET = 'v_inc'
PARAMETERS = {'k_on': 10.0, 'E_crowd': 2.0, 'GE_access': 20.0, 'G_self': 8.0, 'E_self_amp': 1.5}
_symbols = {name: sympy.Symbol(name) for name in ['G', 'E', 'k_on', 'E_crowd', 'GE_access', 'G_self', 'E_self_amp', 'v_inc']}
_expression = sympy.sympify('k_on * G * E / ((1 + G / (G_self / (1 + E / (E_self_amp + E)))) * (1 + E / E_crowd + G * E / GE_access))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
