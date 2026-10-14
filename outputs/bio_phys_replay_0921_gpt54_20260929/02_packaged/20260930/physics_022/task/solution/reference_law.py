"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'T1', 'T2']
TARGET = 'dT1_dt'
PARAMETERS = {'heat_capacity_1': 8000.0, 'heat_capacity_2': 12000.0, 'contact_conductance': 120.0, 'conductance_deltaT_scale': 60.0, 'mean_temperature_conductance_coeff': 0.0015, 'conductance_reference_temperature': 350.0, 'heat_capacity_1_temperature_coeff': 0.001, 'heat_capacity_1_reference_temperature': 350.0, 'body1_contact_temperature_coeff': 0.0008}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'T1', 'T2', 'heat_capacity_1', 'heat_capacity_2', 'contact_conductance', 'conductance_deltaT_scale', 'mean_temperature_conductance_coeff', 'conductance_reference_temperature', 'heat_capacity_1_temperature_coeff', 'heat_capacity_1_reference_temperature', 'body1_contact_temperature_coeff', 'dT1_dt']}
_expression = sympy.sympify('contact_conductance*(1 + mean_temperature_conductance_coeff*((T1 + T2)/2 - conductance_reference_temperature))*(1 + body1_contact_temperature_coeff*(T1 - heat_capacity_1_reference_temperature))*(tanh(Abs(T2 - T1)/conductance_deltaT_scale))**2*(T2 - T1)/(heat_capacity_1*(1 + heat_capacity_1_temperature_coeff*(T1 - heat_capacity_1_reference_temperature)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
