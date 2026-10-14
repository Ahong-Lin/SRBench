"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'N', 'C']
TARGET = 'dN_dt'
PARAMETERS = {'per_capita_birth_rate': 0.8, 'background_mortality_rate': 0.2, 'competition_strength': 0.002, 'crowding_saturation_scale': 0.02, 'crowding_accumulation_rate': 0.015, 'crowding_relaxation_rate': 0.3, 'abundance_crowding_curvature': 0.01, 'high_crowding_compression': 0.5, 'abundance_amplification_compression': 0.005}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'N', 'C', 'per_capita_birth_rate', 'background_mortality_rate', 'competition_strength', 'crowding_saturation_scale', 'crowding_accumulation_rate', 'crowding_relaxation_rate', 'abundance_crowding_curvature', 'high_crowding_compression', 'abundance_amplification_compression', 'dN_dt']}
_expression = sympy.sympify('per_capita_birth_rate*N - background_mortality_rate*N - competition_strength*C*N*(1 + abundance_crowding_curvature*N/(1 + abundance_amplification_compression*N))/(1 + crowding_saturation_scale*C + high_crowding_compression*(crowding_saturation_scale*C)**2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
