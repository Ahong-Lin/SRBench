"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'S', 'I', 'B']
TARGET = 'dI_dt'
PARAMETERS = {'transmission_rate': 2.2, 'removal_rate': 0.5, 'susceptible_saturation': 0.25, 'removal_burden_gain': 1.2, 'removal_burden_saturation': 0.08, 'burden_adjustment_rate': 1.0, 'transmission_burden_gain': 1.0, 'infectious_saturation': 0.08}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'S', 'I', 'B', 'transmission_rate', 'removal_rate', 'susceptible_saturation', 'removal_burden_gain', 'removal_burden_saturation', 'burden_adjustment_rate', 'transmission_burden_gain', 'infectious_saturation', 'dI_dt']}
_expression = sympy.sympify('transmission_rate*S/(susceptible_saturation*(1 + transmission_burden_gain*B/(removal_burden_saturation + B)) + S)*I/(infectious_saturation + I) - removal_rate*(1 + removal_burden_gain*B/(removal_burden_saturation + B))*I', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
