"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['T', 'screening_condition']
TARGET = 'sigma'
PARAMETERS = {'sigma0': 1.0, 'T0': 400.0, 'spatial_dimension': 3.0, 'T1': 150.0, 'channel_scale_ratio': 3.0, 'coulomb_scale_ratio': 0.4}
_symbols = {name: sympy.Symbol(name) for name in ['T', 'screening_condition', 'sigma0', 'T0', 'spatial_dimension', 'T1', 'channel_scale_ratio', 'coulomb_scale_ratio', 'sigma']}
_expression = sympy.sympify('(sigma0 / (1 + screening_condition)) * exp(-(((T0 / (1 + screening_condition * T / T0)) / T)**(1 / (spatial_dimension + 1)) + sqrt(((T1 / (1 + screening_condition)) / T) / (1 + screening_condition * T / (T1 / (1 + screening_condition)))))) + (sigma0 * screening_condition / (1 + screening_condition)) * exp(-((((T0 * channel_scale_ratio) / (1 + screening_condition * T / (T0 * channel_scale_ratio))) / T)**(1 / (spatial_dimension + 1)) + sqrt((((T1 * coulomb_scale_ratio) / (1 + screening_condition)) / T) / (1 + screening_condition * T / ((T1 * coulomb_scale_ratio) / (1 + screening_condition))))))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
