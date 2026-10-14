"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['m1', 'm2', 'v1_before', 'v2_before']
TARGET = 'v1_after'
PARAMETERS = {'collision_efficiency': 0.8, 'reduced_mass_partition_sensitivity': 0.5}
_symbols = {name: sympy.Symbol(name) for name in ['m1', 'm2', 'v1_before', 'v2_before', 'collision_efficiency', 'reduced_mass_partition_sensitivity', 'v1_after']}
_expression = sympy.sympify('(m1*v1_before + m2*v2_before - m2*collision_efficiency*(1 + reduced_mass_partition_sensitivity*(1 - 4*m1*m2/(m1 + m2)**2)/(1 + 4*m1*m2/(m1 + m2)**2))*(1/(1 + Abs(v1_before - v2_before)/(1 + Abs(v1_before - v2_before)) + (Abs(v1_before - v2_before)/(1 + Abs(v1_before - v2_before)))**2))*(((v1_before - v2_before)/(1 + Abs(v1_before - v2_before)))*(1 + Abs(v1_before - v2_before)/(1 + Abs(v1_before - v2_before)))))/(m1 + m2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
