"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['S', 'I', 'Ki']
TARGET = 'v_inh'
PARAMETERS = {'Vmax': 1.5, 'Km': 20.0, 'alpha': 0.8, 'beta': 0.01, 'Ksi': 120.0}
_symbols = {name: sympy.Symbol(name) for name in ['S', 'I', 'Ki', 'Vmax', 'Km', 'alpha', 'beta', 'Ksi', 'v_inh']}
_expression = sympy.sympify('Vmax*S/(Km*(1 + ((I/(Ki + beta*I))*(1 + alpha*I/(Ki + I + S)))) + S + S**2/Ksi)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
