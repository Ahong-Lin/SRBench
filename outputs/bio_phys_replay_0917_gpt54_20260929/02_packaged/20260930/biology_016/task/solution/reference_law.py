"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['V', 'I_cond']
TARGET = 'm_inf'
PARAMETERS = {'V_half': -35.0, 'slope_factor': 9.0, 'I_ref': 1.0, 'ionic_shift_max': 12.0, 'ionic_scale': 0.35, 'slope_ionic_frac': 0.3, 'slope_ionic_scale': 0.4, 'shift_level_frac': 0.45, 'shift_voltage_scale': 14.0, 'shift_curvature_frac': 0.6}
_symbols = {name: sympy.Symbol(name) for name in ['V', 'I_cond', 'V_half', 'slope_factor', 'I_ref', 'ionic_shift_max', 'ionic_scale', 'slope_ionic_frac', 'slope_ionic_scale', 'shift_level_frac', 'shift_voltage_scale', 'shift_curvature_frac', 'm_inf']}
_expression = sympy.sympify('(exp((V - (V_half + ionic_shift_max*tanh((I_cond - I_ref)/ionic_scale)*(1 + shift_level_frac*tanh((V - V_half)/shift_voltage_scale) + shift_curvature_frac*tanh((I_cond - I_ref)/ionic_scale)*tanh((V - V_half)/shift_voltage_scale))))/(slope_factor*(1 + slope_ionic_frac*tanh((I_cond - I_ref)/slope_ionic_scale)))) + exp(2*(V - (V_half + ionic_shift_max*tanh((I_cond - I_ref)/ionic_scale)*(1 + shift_level_frac*tanh((V - V_half)/shift_voltage_scale) + shift_curvature_frac*tanh((I_cond - I_ref)/ionic_scale)*tanh((V - V_half)/shift_voltage_scale))))/(slope_factor*(1 + slope_ionic_frac*tanh((I_cond - I_ref)/slope_ionic_scale)))))/(1 + exp((V - (V_half + ionic_shift_max*tanh((I_cond - I_ref)/ionic_scale)*(1 + shift_level_frac*tanh((V - V_half)/shift_voltage_scale) + shift_curvature_frac*tanh((I_cond - I_ref)/ionic_scale)*tanh((V - V_half)/shift_voltage_scale))))/(slope_factor*(1 + slope_ionic_frac*tanh((I_cond - I_ref)/slope_ionic_scale)))) + exp(2*(V - (V_half + ionic_shift_max*tanh((I_cond - I_ref)/ionic_scale)*(1 + shift_level_frac*tanh((V - V_half)/shift_voltage_scale) + shift_curvature_frac*tanh((I_cond - I_ref)/ionic_scale)*tanh((V - V_half)/shift_voltage_scale))))/(slope_factor*(1 + slope_ionic_frac*tanh((I_cond - I_ref)/slope_ionic_scale)))))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
