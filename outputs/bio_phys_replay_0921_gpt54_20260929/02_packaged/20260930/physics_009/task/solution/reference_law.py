"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['p_0', 'omega', 'r', 'theta']
TARGET = 'S_rad'
PARAMETERS = {'epsilon_0': 8.8541878128e-12, 'c': 299792458.0, 'pi': 3.141592653589793, 'omega_size': 800000000000000.0}
_symbols = {name: sympy.Symbol(name) for name in ['p_0', 'omega', 'r', 'theta', 'epsilon_0', 'c', 'pi', 'omega_size', 'S_rad']}
_expression = sympy.sympify('p_0**2*omega**4*sin(theta)**2*exp(-((omega/omega_size)**2)*(1 + sin(theta)**2/(1 + (omega/omega_size)**2 + ((omega/omega_size)**2)*sin(theta)**2)))/(32*pi**2*epsilon_0*c**3*r**2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
