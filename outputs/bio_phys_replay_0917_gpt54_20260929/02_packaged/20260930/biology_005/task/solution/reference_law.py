"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'N', 'crowding_pressure', 'accumulated_crowding_damage', 'degraded_stress_state']
TARGET = 'dN_dt'
PARAMETERS = {'intrinsic_growth_rate': 0.6, 'carrying_capacity': 1000.0, 'crowding_adjustment_rate': 0.18, 'crowding_nonlinearity_exponent': 2.0, 'damage_accumulation_rate': 0.22, 'damage_relaxation_rate': 0.08, 'crowding_damage_interaction_strength': 1.2, 'stress_state_activation_rate': 0.24, 'stress_state_relaxation_rate': 0.06, 'damage_tolerance_threshold': 250.0, 'stress_state_nonlinearity_exponent': 4.0, 'severe_damage_suppression_strength': 1.5}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'N', 'crowding_pressure', 'accumulated_crowding_damage', 'degraded_stress_state', 'intrinsic_growth_rate', 'carrying_capacity', 'crowding_adjustment_rate', 'crowding_nonlinearity_exponent', 'damage_accumulation_rate', 'damage_relaxation_rate', 'crowding_damage_interaction_strength', 'stress_state_activation_rate', 'stress_state_relaxation_rate', 'damage_tolerance_threshold', 'stress_state_nonlinearity_exponent', 'severe_damage_suppression_strength', 'dN_dt']}
_expression = sympy.sympify('intrinsic_growth_rate*N*(1 - ((crowding_pressure/carrying_capacity) + crowding_damage_interaction_strength*crowding_pressure*accumulated_crowding_damage/carrying_capacity**2)**crowding_nonlinearity_exponent - accumulated_crowding_damage/carrying_capacity - severe_damage_suppression_strength*degraded_stress_state*accumulated_crowding_damage/carrying_capacity)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
