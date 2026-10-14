"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'V_C', 'T_R', 'T_C']
TARGET = 'dV_C_dt'
PARAMETERS = {'resistance': 50.0, 'capacitance': 0.01, 'temp_coeff': 0.004, 'cap_temp_coeff': 0.0005, 'thermal_capacitance': 0.2, 'thermal_resistance': 8.0, 'T_ref': 300.0, 'T_ambient': 300.0, 'resistance_temp_quadratic_coeff': 1e-06, 'cap_thermal_capacitance': 1.5, 'cap_thermal_resistance': 20.0, 'resistor_to_cap_thermal_resistance': 6.0, 'cap_voltage_coeff': 0.002}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'V_C', 'T_R', 'T_C', 'resistance', 'capacitance', 'temp_coeff', 'cap_temp_coeff', 'thermal_capacitance', 'thermal_resistance', 'T_ref', 'T_ambient', 'resistance_temp_quadratic_coeff', 'cap_thermal_capacitance', 'cap_thermal_resistance', 'resistor_to_cap_thermal_resistance', 'cap_voltage_coeff', 'dV_C_dt']}
_expression = sympy.sympify('-V_C/(capacitance*(1 + cap_temp_coeff*(T_C - T_ref))*(1 + cap_voltage_coeff*V_C**2)*resistance*(1 + temp_coeff*(T_R - T_ref) + resistance_temp_quadratic_coeff*(T_R - T_ref)**2))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
