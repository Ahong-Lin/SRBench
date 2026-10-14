"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'V_C', 'I_L', 'T_th']
TARGET = 'dV_C_dt'
PARAMETERS = {'source_voltage': 12.0, 'resistance': 120.0, 'capacitance': 0.001, 'leak_conductance': 0.02, 'leakage_voltage_scale': 2.5, 'capacitance_voltage_nonlinearity': 0.35, 'capacitance_voltage_scale': 4.0, 'parasitic_inductance': 0.02, 'inductive_current_smoothing_scale': 0.12, 'thermal_time_constant': 0.25, 'thermal_heating_gain': 0.06, 'thermal_capacitance_nonlinearity_sensitivity': 0.25, 'thermal_leakage_sensitivity': 0.6}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'V_C', 'I_L', 'T_th', 'source_voltage', 'resistance', 'capacitance', 'leak_conductance', 'leakage_voltage_scale', 'capacitance_voltage_nonlinearity', 'capacitance_voltage_scale', 'parasitic_inductance', 'inductive_current_smoothing_scale', 'thermal_time_constant', 'thermal_heating_gain', 'thermal_capacitance_nonlinearity_sensitivity', 'thermal_leakage_sensitivity', 'dV_C_dt']}
_expression = sympy.sympify('I_L / (capacitance * (1 + capacitance_voltage_nonlinearity * (1 + thermal_capacitance_nonlinearity_sensitivity * T_th) * tanh(Abs(V_C) / capacitance_voltage_scale))) - leak_conductance * (1 + thermal_leakage_sensitivity * T_th) * V_C * tanh(Abs(V_C) / leakage_voltage_scale) / (capacitance * (1 + capacitance_voltage_nonlinearity * (1 + thermal_capacitance_nonlinearity_sensitivity * T_th) * tanh(Abs(V_C) / capacitance_voltage_scale)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
