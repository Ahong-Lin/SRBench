"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'S', 'E', 'R', 'M']
TARGET = 'dS_dt'
PARAMETERS = {'receptor_production_rate': 400.0, 'internalization_rate': 0.08, 'recycling_rate': 350.0, 'endosomal_degradation_rate': 0.05, 'recycling_saturation_scale': 500.0, 'recycling_capacity_recovery_rate': 0.03, 'recycling_capacity_depletion_rate': 0.0002, 'endosomal_maturation_rate': 0.04}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'S', 'E', 'R', 'M', 'receptor_production_rate', 'internalization_rate', 'recycling_rate', 'endosomal_degradation_rate', 'recycling_saturation_scale', 'recycling_capacity_recovery_rate', 'recycling_capacity_depletion_rate', 'endosomal_maturation_rate', 'dS_dt']}
_expression = sympy.sympify('receptor_production_rate - internalization_rate*S + recycling_rate*R*M/(recycling_saturation_scale/R + R*M)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
