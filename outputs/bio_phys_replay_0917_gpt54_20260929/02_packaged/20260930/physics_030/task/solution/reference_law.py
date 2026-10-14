"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'T_h', 'T_c', 'g_contact', 'T_h_interface']
TARGET = 'dT_h_dt'
PARAMETERS = {'contact_conductance': 240.0, 'heat_capacity_h': 5000.0, 'heat_capacity_c': 4200.0, 'conductance_contrast_coeff': 0.004, 'contact_adjustment_time': 80.0, 'hot_capacity_temp_coeff': 1.2, 'hot_capacity_temp_scale': 300.0, 'cold_capacity_temp_coeff': 0.9, 'cold_capacity_temp_scale': 260.0, 'k_internal_hot': 250.0, 'hot_interface_capacity_fraction': 0.12}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'T_h', 'T_c', 'g_contact', 'T_h_interface', 'contact_conductance', 'heat_capacity_h', 'heat_capacity_c', 'conductance_contrast_coeff', 'contact_adjustment_time', 'hot_capacity_temp_coeff', 'hot_capacity_temp_scale', 'cold_capacity_temp_coeff', 'cold_capacity_temp_scale', 'k_internal_hot', 'hot_interface_capacity_fraction', 'dT_h_dt']}
_expression = sympy.sympify('-k_internal_hot*(T_h - T_h_interface)/(heat_capacity_h*(1 + hot_capacity_temp_coeff*T_h/(hot_capacity_temp_scale + T_h)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
