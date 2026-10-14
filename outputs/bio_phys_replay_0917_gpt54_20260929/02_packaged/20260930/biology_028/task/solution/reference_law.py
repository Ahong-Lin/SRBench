"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'L', 'C', 'I_late', 'C_latent']
TARGET = 'dC_dt'
PARAMETERS = {'progression_rate': 0.22, 'clearance_rate': 0.32, 'stage_progression_rate': 0.18, 'late_half_saturation': 120.0, 'inflow_clearance_modulation': 3.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'L', 'C', 'I_late', 'C_latent', 'progression_rate', 'clearance_rate', 'stage_progression_rate', 'late_half_saturation', 'inflow_clearance_modulation', 'dC_dt']}
_expression = sympy.sympify('progression_rate*C_latent - clearance_rate*C*I_late/((late_half_saturation*(1 + inflow_clearance_modulation*progression_rate*C_latent/(late_half_saturation + progression_rate*C_latent)))*(1 + C/late_half_saturation) + I_late)*(late_half_saturation + C)/(late_half_saturation + 2*C)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
