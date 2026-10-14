"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['Delta', 'T', 'g_occ']
TARGET = 'n_bar'
PARAMETERS = {'g_emp': 1.0, 'c_ex': 0.15, 'c_ex3': -0.03, 'c_ex4': 0.005, 'c_occ_ex': 0.6}
_symbols = {name: sympy.Symbol(name) for name in ['Delta', 'T', 'g_occ', 'g_emp', 'c_ex', 'c_ex3', 'c_ex4', 'c_occ_ex', 'n_bar']}
_expression = sympy.sympify('1/(exp((Delta + c_ex*T**2 + c_ex3*T**3 + c_ex4*T**4 - T*log((g_occ*(1 + c_occ_ex*T/(1 + T)))/g_emp))/T) + 1)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
