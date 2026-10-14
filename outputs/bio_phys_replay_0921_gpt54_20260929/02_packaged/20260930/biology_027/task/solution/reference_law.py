"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'P_a', 'u', 'v', 'w']
TARGET = 'dP_a_dt'
PARAMETERS = {'P_set': 100.0, 'u_baseline': 0.5, 'autonomic_pressure_gain': 28.0, 'pressure_time_constant': 5.0, 'autonomic_time_constant': 3.0, 'baroreflex_sensitivity': 0.08, 'pressure_efficacy_error_gain': 0.03, 'slow_support_weight': 0.6, 'slow_autonomic_time_constant': 12.0, 'hemodynamic_transduction_time_constant': 4.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'P_a', 'u', 'v', 'w', 'P_set', 'u_baseline', 'autonomic_pressure_gain', 'pressure_time_constant', 'autonomic_time_constant', 'baroreflex_sensitivity', 'pressure_efficacy_error_gain', 'slow_support_weight', 'slow_autonomic_time_constant', 'hemodynamic_transduction_time_constant', 'dP_a_dt']}
_expression = sympy.sympify('(P_set + autonomic_pressure_gain*w*(1 + (pressure_efficacy_error_gain*(P_set - P_a))/(1 + Abs(pressure_efficacy_error_gain*(P_set - P_a)))) - P_a)/pressure_time_constant', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
