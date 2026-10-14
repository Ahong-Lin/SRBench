"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'C1', 'C2', 'mixing_efficiency', 'shielding_memory']
TARGET = 'dC1_dt'
PARAMETERS = {'exchange_rate': 0.8, 'saturation_contrast': 0.8, 'mixing_relaxation_rate': 0.7, 'contrast_mixing_coupling': 1.4, 'mixing_baseline': 0.6, 'crowding_sharpness': 0.6, 'shielding_build_rate': 0.9, 'shielding_relaxation_rate': 0.45}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'C1', 'C2', 'mixing_efficiency', 'shielding_memory', 'exchange_rate', 'saturation_contrast', 'mixing_relaxation_rate', 'contrast_mixing_coupling', 'mixing_baseline', 'crowding_sharpness', 'shielding_build_rate', 'shielding_relaxation_rate', 'dC1_dt']}
_expression = sympy.sympify('exchange_rate*mixing_efficiency*(C2 - C1)/(1 + saturation_contrast*((1 + shielding_memory)*mixing_efficiency*Abs(C2 - C1))**2 + crowding_sharpness*(saturation_contrast*((1 + shielding_memory)*mixing_efficiency*Abs(C2 - C1))**2)**2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
