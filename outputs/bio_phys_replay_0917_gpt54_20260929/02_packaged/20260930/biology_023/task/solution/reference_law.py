"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'C', 'A', 'D']
TARGET = 'dC_dt'
PARAMETERS = {'k_cyclin_synthesis': 0.25, 'k_cyclin_degradation': 2.5, 'K_cyclin_degradation_saturation': 0.7, 'k_regulator_activation': 1.8, 'K_cyclin_activation': 0.8, 'n_cyclin': 4.0, 'activation_seed': 0.08, 'K_regulator_feedback': 0.35, 'n_regulator': 4.0, 'k_regulator_relaxation': 0.45, 'k_degradation_capacity_maturation': 0.6, 'K_degradation_capacity_activation': 0.25}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'C', 'A', 'D', 'k_cyclin_synthesis', 'k_cyclin_degradation', 'K_cyclin_degradation_saturation', 'k_regulator_activation', 'K_cyclin_activation', 'n_cyclin', 'activation_seed', 'K_regulator_feedback', 'n_regulator', 'k_regulator_relaxation', 'k_degradation_capacity_maturation', 'K_degradation_capacity_activation', 'dC_dt']}
_expression = sympy.sympify('k_cyclin_synthesis - k_cyclin_degradation*(D**2/(K_degradation_capacity_activation*D + D**2))*(A/(K_degradation_capacity_activation + A))*C/(K_cyclin_degradation_saturation/(1 + D/(K_degradation_capacity_activation + D)) + C)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
