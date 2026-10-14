"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['m1', 'm2', 'u1', 'u2']
TARGET = 'v_post'
PARAMETERS = {}
_symbols = {name: sympy.Symbol(name) for name in ['m1', 'm2', 'u1', 'u2', 'v_post']}
_expression = sympy.sympify('(m1*u1 + m2*u2 - (m1*m2/(m1 + m2))*(u1 - u2)*(1 + ((4*m1*m2/(m1 + m2)**2)*((u1 - u2)/((m1*u1 + m2*u2)/(m1 + m2)))**2)/(1 + (4*m1*m2/(m1 + m2)**2)*((u1 - u2)/((m1*u1 + m2*u2)/(m1 + m2)))**2) + ((4*m1*m2/(m1 + m2)**2)**2*((u1 - u2)/((m1*u1 + m2*u2)/(m1 + m2)))**4)/(1 + (4*m1*m2/(m1 + m2)**2)*((u1 - u2)/((m1*u1 + m2*u2)/(m1 + m2)))**2)**2)*tanh(((u1 - u2)/((m1*u1 + m2*u2)/(m1 + m2)))*(1 + (4*m1*m2/(m1 + m2)**2)*((u1 - u2)/((m1*u1 + m2*u2)/(m1 + m2)))**2)))/(m1 + m2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
