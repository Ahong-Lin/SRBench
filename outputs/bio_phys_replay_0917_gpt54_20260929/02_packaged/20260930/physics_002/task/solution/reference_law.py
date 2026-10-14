"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'T_A', 'T_B', 'effective_conductance']
TARGET = 'dT_A_dt'
PARAMETERS = {'heat_capacity_A': 100.0, 'heat_capacity_B': 120.0, 'thermal_conductance': 1.5, 'conductance_temp_coeff': 0.001, 'contrast_nonlinearity_coeff': 5e-05, 'conductance_relaxation_time': 25.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'T_A', 'T_B', 'effective_conductance', 'heat_capacity_A', 'heat_capacity_B', 'thermal_conductance', 'conductance_temp_coeff', 'contrast_nonlinearity_coeff', 'conductance_relaxation_time', 'dT_A_dt']}
_expression = sympy.sympify('effective_conductance*(T_B - T_A)/(heat_capacity_A*(1 + contrast_nonlinearity_coeff*(1 + conductance_temp_coeff*(T_A + T_B)/2)*(T_B - T_A)**2))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
