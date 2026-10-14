"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['n', 'L', 'm', 'V0']
TARGET = 'En'
PARAMETERS = {'hbar': 1.0}
_symbols = {name: sympy.Symbol(name) for name in ['n', 'L', 'm', 'V0', 'hbar', 'En']}
_expression = sympy.sympify('Piecewise((V0 - hbar**2*n**2*pi**2/(2*m*L**2) - V0*hbar**2*n**2*pi**2/(12*m*L**2*(V0 + hbar**2*n**2*pi**2/(2*m*L**2))), L*sqrt(2*m*V0)/hbar >= n*pi), (V0 - hbar**2*n**2*pi**2/(2*m*L**2) + hbar**2/L**2*(sqrt(2*m*V0)*L/hbar - n*pi)*tanh(sqrt(2*m*V0)*L/hbar - n*pi) - V0*hbar**2*n**2*pi**2/(12*m*L**2*(V0 + hbar**2*n**2*pi**2/(2*m*L**2))), True))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
