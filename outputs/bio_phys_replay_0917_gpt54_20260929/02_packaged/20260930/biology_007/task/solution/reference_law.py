"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'N1', 'N2', 'propensity', 'adaptation_rate']
TARGET = 'dN1_dt'
PARAMETERS = {'dispersal_rate': 0.003, 'crowding_sensitivity': 2.0, 'crowding_saturation': 0.005, 'adaptation_relaxation_rate': 0.08, 'adaptation_crowding_sensitivity': 1.5, 'adaptation_crowding_saturation': 0.01}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'N1', 'N2', 'propensity', 'adaptation_rate', 'dispersal_rate', 'crowding_sensitivity', 'crowding_saturation', 'adaptation_relaxation_rate', 'adaptation_crowding_sensitivity', 'adaptation_crowding_saturation', 'dN1_dt']}
_expression = sympy.sympify('dispersal_rate*N2*propensity*(1 + crowding_sensitivity*N2/(1 + crowding_saturation*(N1 + N2))) - dispersal_rate*N1*(1 + crowding_sensitivity*N1/(1 + crowding_saturation*(N1 + N2)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
