"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'J', 'A', 'maturation_rate']
TARGET = 'dA_dt'
PARAMETERS = {'juvenile_recruitment_rate': 0.06, 'juvenile_mortality_rate': 0.03, 'adult_mortality_rate': 0.03, 'juvenile_crowding_coefficient': 0.01, 'adult_density_loss_coefficient': 0.015, 'adult_density_half_saturation_coefficient': 0.01, 'juvenile_crowding_quadratic_coefficient': 2e-05, 'adult_maturation_inhibition_coefficient': 8e-05, 'maturation_capacity_recovery_rate': 0.08, 'maturation_capacity_stress_sensitivity': 0.0008, 'baseline_maturation_rate': 1.2}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'J', 'A', 'maturation_rate', 'juvenile_recruitment_rate', 'juvenile_mortality_rate', 'adult_mortality_rate', 'juvenile_crowding_coefficient', 'adult_density_loss_coefficient', 'adult_density_half_saturation_coefficient', 'juvenile_crowding_quadratic_coefficient', 'adult_maturation_inhibition_coefficient', 'maturation_capacity_recovery_rate', 'maturation_capacity_stress_sensitivity', 'baseline_maturation_rate', 'dA_dt']}
_expression = sympy.sympify('maturation_rate*J/(1 + juvenile_crowding_coefficient*J + juvenile_crowding_quadratic_coefficient*J**2 + adult_maturation_inhibition_coefficient*A*J) - adult_mortality_rate*A*(1 + adult_density_loss_coefficient*A/(1 + adult_density_half_saturation_coefficient*A))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
