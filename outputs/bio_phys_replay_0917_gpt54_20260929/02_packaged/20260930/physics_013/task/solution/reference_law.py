"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'omega', 'resistance_coefficient', 'baseline_resistance_coefficient', 'cooling_time_constant']
TARGET = 'domega_dt'
PARAMETERS = {'drive_torque': 6.0, 'nonlinear_drag_coefficient': 0.15, 'speed_transition': 2.0, 'rotor_inertia': 1.5, 'thermal_sensitivity': 0.04, 'thermal_drag_sensitivity': 0.6, 'thermal_drag_scale': 0.4, 'baseline_drift_sensitivity': 0.008, 'baseline_relaxation_time_constant': 30.0, 'cooling_heat_sensitivity': 0.02, 'cooling_recovery_time_constant': 12.0, 'nominal_cooling_time_constant': 1.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'omega', 'resistance_coefficient', 'baseline_resistance_coefficient', 'cooling_time_constant', 'drive_torque', 'nonlinear_drag_coefficient', 'speed_transition', 'rotor_inertia', 'thermal_sensitivity', 'thermal_drag_sensitivity', 'thermal_drag_scale', 'baseline_drift_sensitivity', 'baseline_relaxation_time_constant', 'cooling_heat_sensitivity', 'cooling_recovery_time_constant', 'nominal_cooling_time_constant', 'domega_dt']}
_expression = sympy.sympify('(drive_torque - resistance_coefficient * omega - nonlinear_drag_coefficient * (1 + thermal_drag_sensitivity * (resistance_coefficient - baseline_resistance_coefficient) / (thermal_drag_scale + Abs(resistance_coefficient - baseline_resistance_coefficient))) * omega**3 / (speed_transition + Abs(omega))) / rotor_inertia', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
