"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'T_c', 'H', 'H_slow', 'metabolic_heat_production']
TARGET = 'dT_c_dt'
PARAMETERS = {'effective_heat_capacity': 250000.0, 'heat_loss_sensitivity': 0.9, 'thermal_set_point': 37.0, 'heat_loss_curvature': 0.18, 'thermoeffector_adjustment_time': 600.0, 'recruitment_time_acceleration': 0.9, 'recruitment_activation_scale': 0.4, 'slow_effector_weight': 0.35, 'slow_recruitment_time': 1800.0, 'slow_recruitment_threshold': 0.3, 'metabolic_suppression_strength': 0.25, 'metabolic_adjustment_time': 3600.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'T_c', 'H', 'H_slow', 'metabolic_heat_production', 'effective_heat_capacity', 'heat_loss_sensitivity', 'thermal_set_point', 'heat_loss_curvature', 'thermoeffector_adjustment_time', 'recruitment_time_acceleration', 'recruitment_activation_scale', 'slow_effector_weight', 'slow_recruitment_time', 'slow_recruitment_threshold', 'metabolic_suppression_strength', 'metabolic_adjustment_time', 'dT_c_dt']}
_expression = sympy.sympify('(metabolic_heat_production - metabolic_heat_production*((1 - slow_effector_weight)*H + slow_effector_weight*H_slow))/effective_heat_capacity', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
