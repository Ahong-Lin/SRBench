"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'J', 'A', 'D']
TARGET = 'dA_dt'
PARAMETERS = {'fecundity_rate': 1.4, 'carrying_capacity': 500.0, 'maturation_rate': 0.8, 'juvenile_mortality_rate': 0.2, 'adult_mortality_rate': 0.15, 'adult_crowding_coefficient': 0.001, 'stress_accumulation_rate': 1.2, 'stress_recovery_rate': 0.35, 'developmental_stress_sensitivity': 0.6}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'J', 'A', 'D', 'fecundity_rate', 'carrying_capacity', 'maturation_rate', 'juvenile_mortality_rate', 'adult_mortality_rate', 'adult_crowding_coefficient', 'stress_accumulation_rate', 'stress_recovery_rate', 'developmental_stress_sensitivity', 'dA_dt']}
_expression = sympy.sympify('maturation_rate*exp(-developmental_stress_sensitivity*D)*J*(J/(J + carrying_capacity))/((1 + (J + A)/carrying_capacity)*(1 + J/carrying_capacity)) - adult_mortality_rate*A - adult_crowding_coefficient*A**2', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
