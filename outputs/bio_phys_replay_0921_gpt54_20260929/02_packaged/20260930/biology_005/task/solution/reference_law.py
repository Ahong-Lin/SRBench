"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'V', 'A', 'membrane_capacitance', 'G']
TARGET = 'dV_dt'
PARAMETERS = {'applied_current': 120.0, 'leak_conductance': 10.0, 'resting_voltage': -65.0, 'adaptation_gain': 4.0, 'adaptation_time_constant': 120.0, 'leak_rectification_strength': 0.002, 'adaptation_saturation_scale': 15.0, 'capacitance_recruitment_gain': 0.6, 'capacitance_time_constant': 150.0, 'capacitance_recruitment_scale': 12.0, 'baseline_membrane_capacitance': 1.0, 'adaptation_reversal_voltage': -80.0, 'adaptation_conductance_saturation_scale': 20.0, 'adaptation_availability_time_constant': 250.0, 'adaptation_inactivation_gain': 0.5, 'adaptation_inactivation_scale': 12.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'V', 'A', 'membrane_capacitance', 'G', 'applied_current', 'leak_conductance', 'resting_voltage', 'adaptation_gain', 'adaptation_time_constant', 'leak_rectification_strength', 'adaptation_saturation_scale', 'capacitance_recruitment_gain', 'capacitance_time_constant', 'capacitance_recruitment_scale', 'baseline_membrane_capacitance', 'adaptation_reversal_voltage', 'adaptation_conductance_saturation_scale', 'adaptation_availability_time_constant', 'adaptation_inactivation_gain', 'adaptation_inactivation_scale', 'dV_dt']}
_expression = sympy.sympify('(applied_current - leak_conductance*(1 + leak_rectification_strength*(V - resting_voltage)**2)*(V - resting_voltage) - G*A*(V - adaptation_reversal_voltage)*adaptation_conductance_saturation_scale/((V - adaptation_reversal_voltage) + adaptation_conductance_saturation_scale))/membrane_capacitance', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
