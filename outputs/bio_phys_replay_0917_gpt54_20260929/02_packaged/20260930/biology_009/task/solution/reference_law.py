"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'p', 'selection_coefficient', 'attenuation_occupancy', 'delayed_burden']
TARGET = 'dp_dt'
PARAMETERS = {'selection_decay_rate': 0.6, 'selection_capacity': 0.5, 'occupancy_buildup_rate': 1.2, 'occupancy_relaxation_rate': 0.35, 'attenuation_capacity': 2.0, 'asymmetry_strength': 1.6, 'asymmetry_threshold': 0.3, 'burden_buildup_rate': 1.8, 'burden_relaxation_rate': 0.45, 'burden_half_saturation': 1.5}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'p', 'selection_coefficient', 'attenuation_occupancy', 'delayed_burden', 'selection_decay_rate', 'selection_capacity', 'occupancy_buildup_rate', 'occupancy_relaxation_rate', 'attenuation_capacity', 'asymmetry_strength', 'asymmetry_threshold', 'burden_buildup_rate', 'burden_relaxation_rate', 'burden_half_saturation', 'dp_dt']}
_expression = sympy.sympify('selection_coefficient*p*(1 - p)*(1 + asymmetry_strength*(1 - p)/(asymmetry_threshold + 1 - p))/(1 + delayed_burden/attenuation_capacity + (delayed_burden/attenuation_capacity)**2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
