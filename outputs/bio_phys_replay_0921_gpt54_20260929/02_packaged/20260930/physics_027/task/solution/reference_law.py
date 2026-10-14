"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'x', 'v', 'internal_loss_level', 'loss_activation_level']
TARGET = 'dv_dt'
PARAMETERS = {'mass': 1.0, 'spring_stiffness': 4.0, 'damping_coefficient': 0.25, 'cubic_stiffness': 1.2, 'nonlinear_damping_strength': 0.4, 'loss_drive_rate': 0.35, 'loss_relaxation_rate': 0.12, 'loss_activation_rate': 0.5, 'loss_saturation_scale': 0.8}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'x', 'v', 'internal_loss_level', 'loss_activation_level', 'mass', 'spring_stiffness', 'damping_coefficient', 'cubic_stiffness', 'nonlinear_damping_strength', 'loss_drive_rate', 'loss_relaxation_rate', 'loss_activation_rate', 'loss_saturation_scale', 'dv_dt']}
_expression = sympy.sympify('-(spring_stiffness/mass)*x - (damping_coefficient/mass)*(1 + internal_loss_level)*(1 + nonlinear_damping_strength*v**2/(1 + nonlinear_damping_strength*v**2))*v - (cubic_stiffness/mass)*x**3', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
