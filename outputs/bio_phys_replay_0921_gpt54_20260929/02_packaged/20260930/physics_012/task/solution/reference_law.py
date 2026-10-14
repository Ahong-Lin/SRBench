"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'N_P', 'N_D', 'daughter_decay_constant', 'damage_capacity']
TARGET = 'dN_D_dt'
PARAMETERS = {'parent_decay_constant': 0.02, 'damage_drive_rate': 0.0004, 'damage_relaxation_rate': 0.03, 'capacity_growth_rate': 0.00015, 'capacity_relaxation_rate': 0.015, 'baseline_damage_capacity': 5000.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'N_P', 'N_D', 'daughter_decay_constant', 'damage_capacity', 'parent_decay_constant', 'damage_drive_rate', 'damage_relaxation_rate', 'capacity_growth_rate', 'capacity_relaxation_rate', 'baseline_damage_capacity', 'dN_D_dt']}
_expression = sympy.sympify('parent_decay_constant*N_P - daughter_decay_constant*N_D/((1 + N_D/damage_capacity)*(1 + (N_D/damage_capacity)**2)*(1 + daughter_decay_constant/damage_capacity))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
