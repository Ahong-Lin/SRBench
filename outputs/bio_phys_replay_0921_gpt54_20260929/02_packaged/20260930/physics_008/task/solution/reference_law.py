"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['Z_1', 'Z_2', 'Z_layer', 'phi_layer']
TARGET = 'R_P'
PARAMETERS = {}
_symbols = {name: sympy.Symbol(name) for name in ['Z_1', 'Z_2', 'Z_layer', 'phi_layer', 'R_P']}
_expression = sympy.sympify('((((Z_layer - Z_1)/(Z_layer + Z_1) + ((Z_2 - Z_layer)/(Z_2 + Z_layer))*cos(phi_layer))/((1 + ((Z_layer - Z_1)/(Z_layer + Z_1))*((Z_2 - Z_layer)/(Z_2 + Z_layer))*cos(phi_layer))**2 + ((((Z_layer - Z_1)/(Z_layer + Z_1))*((Z_2 - Z_layer)/(Z_2 + Z_layer)))*sin(phi_layer))**2))**2 + ((((Z_2 - Z_layer)/(Z_2 + Z_layer))*sin(phi_layer))/((1 + ((Z_layer - Z_1)/(Z_layer + Z_1))*((Z_2 - Z_layer)/(Z_2 + Z_layer))*cos(phi_layer))**2 + ((((Z_layer - Z_1)/(Z_layer + Z_1))*((Z_2 - Z_layer)/(Z_2 + Z_layer)))*sin(phi_layer))**2))**2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
