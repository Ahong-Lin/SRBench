"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'T_c', 'effector_recruitment_state']
TARGET = 'dT_c_dt'
PARAMETERS = {'basal_heat_production': 8.0, 'environmental_heat_transfer_coefficient': 1.2, 'ambient_temperature': 25.0, 'thermoregulatory_feedback_gain': 10.0, 'core_temperature_set_point': 37.0, 'effective_heat_capacity': 60.0, 'feedback_recruitment_temperature_scale': 0.5, 'heat_capacity_temperature_sensitivity': 0.3, 'effector_adjustment_time_constant': 12.0, 'effector_kinetic_asymmetry': 0.45}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'T_c', 'effector_recruitment_state', 'basal_heat_production', 'environmental_heat_transfer_coefficient', 'ambient_temperature', 'thermoregulatory_feedback_gain', 'core_temperature_set_point', 'effective_heat_capacity', 'feedback_recruitment_temperature_scale', 'heat_capacity_temperature_sensitivity', 'effector_adjustment_time_constant', 'effector_kinetic_asymmetry', 'dT_c_dt']}
_expression = sympy.sympify('(basal_heat_production - environmental_heat_transfer_coefficient*(T_c - ambient_temperature) - thermoregulatory_feedback_gain*effector_recruitment_state*(feedback_recruitment_temperature_scale*tanh((T_c - core_temperature_set_point)/feedback_recruitment_temperature_scale)))/(effective_heat_capacity*(1 + heat_capacity_temperature_sensitivity*((T_c - core_temperature_set_point)/feedback_recruitment_temperature_scale)**2))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
