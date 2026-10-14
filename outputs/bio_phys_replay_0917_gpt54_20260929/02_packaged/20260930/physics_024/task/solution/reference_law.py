"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'q', 'i', 'resistance', 'capacitance']
TARGET = 'di_dt'
PARAMETERS = {'inductance': 0.5, 'resistance_nonlinear_coeff': 0.8, 'thermal_resistance_gain': 0.6, 'thermal_capacity': 8.0, 'ambient_resistance': 1.0, 'heating_saturation_power': 0.02, 'saturation_current_scale': 0.08, 'capacitance_relaxation_time': 0.03, 'small_signal_capacitance': 0.001, 'capacitance_field_gain': 0.4, 'capacitance_field_scale': 0.001}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'q', 'i', 'resistance', 'capacitance', 'inductance', 'resistance_nonlinear_coeff', 'thermal_resistance_gain', 'thermal_capacity', 'ambient_resistance', 'heating_saturation_power', 'saturation_current_scale', 'capacitance_relaxation_time', 'small_signal_capacitance', 'capacitance_field_gain', 'capacitance_field_scale', 'di_dt']}
_expression = sympy.sympify('(-(resistance + resistance_nonlinear_coeff*Abs(i))*i - q/(capacitance*(1 + capacitance_relaxation_time*Abs(i)/sqrt(inductance*small_signal_capacitance))))/(inductance/(1 + Abs(i)/saturation_current_scale))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
