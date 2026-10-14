"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['M', 'r', 'R_body', 'spin_rate']
TARGET = 'v_orbit'
PARAMETERS = {'G': 0.001, 'oblateness_coeff': 0.35, 'frame_drag_coeff': 0.6, 'higher_multipole_coeff': 0.25}
_symbols = {name: sympy.Symbol(name) for name in ['M', 'r', 'R_body', 'spin_rate', 'G', 'oblateness_coeff', 'frame_drag_coeff', 'higher_multipole_coeff', 'v_orbit']}
_expression = sympy.sympify('sqrt((G*M/r)/(1 - 3*G*M/r)*(1 + oblateness_coeff*(R_body**2/r**2)/(1 + R_body**2/r**2) + higher_multipole_coeff*R_body**4/r**4) - frame_drag_coeff*spin_rate*sqrt(G*M/r)*R_body**2/r**2/(1 - 3*G*M/r))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
