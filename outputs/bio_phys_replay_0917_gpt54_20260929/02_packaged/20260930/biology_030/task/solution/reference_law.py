"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'N', 'crowding_memory', 'crowding_sensitivity']
TARGET = 'dN_dt'
PARAMETERS = {'intrinsic_growth_rate': 0.6, 'carrying_capacity': 1000.0, 'crowding_exponent': 2.5, 'crowding_adjustment_rate': 0.12, 'crowding_sensitivity_adjustment_rate': 0.3, 'crowding_mismatch_sensitivity': 1.5, 'crowding_threshold_shift_strength': 1.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'N', 'crowding_memory', 'crowding_sensitivity', 'intrinsic_growth_rate', 'carrying_capacity', 'crowding_exponent', 'crowding_adjustment_rate', 'crowding_sensitivity_adjustment_rate', 'crowding_mismatch_sensitivity', 'crowding_threshold_shift_strength', 'dN_dt']}
_expression = sympy.sympify('intrinsic_growth_rate*N*(1 - ((((crowding_sensitivity*N + (2 - crowding_sensitivity)*crowding_memory)/(2*carrying_capacity))*(1 + crowding_threshold_shift_strength*(N - crowding_memory)/carrying_capacity))**crowding_exponent))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
