"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'S', 'I', 'R', 'I_phase']
TARGET = 'dI_dt'
PARAMETERS = {'transmission_rate': 1.8, 'recovery_rate': 0.6, 'saturation_strength': 8.0, 'phase_progression_rate': 1.2, 'phase_saturation': 4.0, 'phase_curvature_strength': 2.0, 'late_phase_share_saturation': 10.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'S', 'I', 'R', 'I_phase', 'transmission_rate', 'recovery_rate', 'saturation_strength', 'phase_progression_rate', 'phase_saturation', 'phase_curvature_strength', 'late_phase_share_saturation', 'dI_dt']}
_expression = sympy.sympify('transmission_rate*S*I/(1 + saturation_strength*(I + I_phase + phase_curvature_strength*I_phase**2/(1 + late_phase_share_saturation*I_phase))) - recovery_rate*I_phase/(1 + phase_saturation*I_phase)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
