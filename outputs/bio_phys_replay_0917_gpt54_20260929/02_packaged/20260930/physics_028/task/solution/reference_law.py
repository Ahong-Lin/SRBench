"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'theta', 'omega', 'wake_intensity']
TARGET = 'domega_dt'
PARAMETERS = {'mass': 1.0, 'gravity': 9.81, 'center_of_mass_distance': 0.5, 'moment_of_inertia': 0.25, 'damping_coefficient': 0.08, 'quadratic_drag_coefficient': 0.02, 'wake_relaxation_time': 0.8, 'wake_drive_gain': 0.06, 'aerodynamic_stiffness_gain': 0.7, 'amplitude_softening_gain': 0.8}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'theta', 'omega', 'wake_intensity', 'mass', 'gravity', 'center_of_mass_distance', 'moment_of_inertia', 'damping_coefficient', 'quadratic_drag_coefficient', 'wake_relaxation_time', 'wake_drive_gain', 'aerodynamic_stiffness_gain', 'amplitude_softening_gain', 'domega_dt']}
_expression = sympy.sympify('-(mass * gravity * center_of_mass_distance / moment_of_inertia) * sin(theta) / (1 + aerodynamic_stiffness_gain * (1 + amplitude_softening_gain * (1 - cos(theta))) * Max(wake_intensity - 1, 0)) - (damping_coefficient / moment_of_inertia) * omega - (quadratic_drag_coefficient / moment_of_inertia) * wake_intensity * omega * Abs(omega)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
