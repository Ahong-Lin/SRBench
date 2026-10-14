"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'eta', 'u', 'depth_compression', 'shape_lag']
TARGET = 'du_dt'
PARAMETERS = {'gravity': 9.81, 'wavenumber': 1.2, 'linear_damping_rate': 0.08, 'quadratic_damping_rate': 0.12, 'velocity_transition_scale': 0.08, 'finite_amplitude_stiffening': 80.0, 'depth_relaxation_rate': 2.0, 'depth_saturation_scale': 0.12, 'geometry_drag_sensitivity': 0.8, 'shape_lag_relaxation_rate': 3.0, 'dynamic_stiffness_phase_sensitivity': 0.4}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'eta', 'u', 'depth_compression', 'shape_lag', 'gravity', 'wavenumber', 'linear_damping_rate', 'quadratic_damping_rate', 'velocity_transition_scale', 'finite_amplitude_stiffening', 'depth_relaxation_rate', 'depth_saturation_scale', 'geometry_drag_sensitivity', 'shape_lag_relaxation_rate', 'dynamic_stiffness_phase_sensitivity', 'du_dt']}
_expression = sympy.sympify('-gravity * wavenumber * eta * (1 + finite_amplitude_stiffening * depth_compression * (1 + dynamic_stiffness_phase_sensitivity * shape_lag / depth_saturation_scale)) - linear_damping_rate * u - quadratic_damping_rate * (1 + geometry_drag_sensitivity * depth_compression / depth_saturation_scale**2) * u * Abs(u) / (velocity_transition_scale + Abs(u))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
