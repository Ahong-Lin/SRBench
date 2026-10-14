"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['R', 'attack_rate', 'resource_quality']
TARGET = 'F'
PARAMETERS = {'handling_time': 0.5, 'handling_crowding_scale': 0.2, 'resource_crowding_half_sat': 0.1, 'quality_handling_scale': 1.0, 'resource_quality_half_sat': 1.0, 'quality_attack_coupling': 1.0}
_symbols = {name: sympy.Symbol(name) for name in ['R', 'attack_rate', 'resource_quality', 'handling_time', 'handling_crowding_scale', 'resource_crowding_half_sat', 'quality_handling_scale', 'resource_quality_half_sat', 'quality_attack_coupling', 'F']}
_expression = sympy.sympify('attack_rate*R/(1 + attack_rate*(handling_time*(1 + quality_handling_scale*(1 + quality_attack_coupling*attack_rate)/(1 + resource_quality_half_sat*resource_quality)) + handling_crowding_scale*attack_rate*R/(1 + resource_crowding_half_sat*R))*R)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
