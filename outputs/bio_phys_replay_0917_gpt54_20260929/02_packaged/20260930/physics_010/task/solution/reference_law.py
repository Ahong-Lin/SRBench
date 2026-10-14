"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'x', 'v', 'z', 'c']
TARGET = 'dv_dt'
PARAMETERS = {'mass': 1.0, 'spring_constant': 12.0, 'damping_coefficient': 0.8, 'cubic_stiffness_coefficient': 1.5, 'nonlinear_drag_coefficient': 0.25, 'relaxation_time': 0.7, 'conditioning_rate': 0.9, 'conditioning_strain_coefficient': 0.6, 'saturation_strain_coefficient': 0.8}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'x', 'v', 'z', 'c', 'mass', 'spring_constant', 'damping_coefficient', 'cubic_stiffness_coefficient', 'nonlinear_drag_coefficient', 'relaxation_time', 'conditioning_rate', 'conditioning_strain_coefficient', 'saturation_strain_coefficient', 'dv_dt']}
_expression = sympy.sympify('-((spring_constant * (1 + (cubic_stiffness_coefficient * z**2) / (1 + saturation_strain_coefficient * z**2))) / mass) * z - (damping_coefficient / mass) * v - (nonlinear_drag_coefficient / mass) * Abs(v) * v', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
