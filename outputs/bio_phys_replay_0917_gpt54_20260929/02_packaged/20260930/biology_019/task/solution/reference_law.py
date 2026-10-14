"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['pH', 'ionic_strength']
TARGET = 'k_app'
PARAMETERS = {'k_cat_competent': 100.0, 'pKa_protonated_group': 6.2, 'pKa_deprotonated_group': 8.0, 'ionic_strength_sensitivity_protonated_group': 0.8, 'ionic_strength_sensitivity_deprotonated_group': -0.6, 'ionic_strength_half_saturation': 0.15, 'ionic_strength_turnover_sensitivity': 1.2, 'ionic_strength_turnover_half_saturation': 0.08, 'competent_state_pH_turnover_sensitivity': 0.15, 'protonated_group_hill_coefficient': 1.3}
_symbols = {name: sympy.Symbol(name) for name in ['pH', 'ionic_strength', 'k_cat_competent', 'pKa_protonated_group', 'pKa_deprotonated_group', 'ionic_strength_sensitivity_protonated_group', 'ionic_strength_sensitivity_deprotonated_group', 'ionic_strength_half_saturation', 'ionic_strength_turnover_sensitivity', 'ionic_strength_turnover_half_saturation', 'competent_state_pH_turnover_sensitivity', 'protonated_group_hill_coefficient', 'k_app']}
_expression = sympy.sympify('(k_cat_competent*(1 + ionic_strength_turnover_sensitivity*ionic_strength/(ionic_strength_turnover_half_saturation + ionic_strength))*(1 + competent_state_pH_turnover_sensitivity*ionic_strength/(ionic_strength_turnover_half_saturation + ionic_strength)*(pH - ((pKa_protonated_group + ionic_strength_sensitivity_protonated_group*ionic_strength/(ionic_strength_half_saturation + ionic_strength)) + (pKa_deprotonated_group + ionic_strength_sensitivity_deprotonated_group*ionic_strength/(ionic_strength_half_saturation + ionic_strength)))/2)))/((1 + 10**(protonated_group_hill_coefficient*(pH - (pKa_protonated_group + ionic_strength_sensitivity_protonated_group*ionic_strength/(ionic_strength_half_saturation + ionic_strength)))))*(1 + 10**((pKa_deprotonated_group + ionic_strength_sensitivity_deprotonated_group*ionic_strength/(ionic_strength_half_saturation + ionic_strength)) - pH)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
