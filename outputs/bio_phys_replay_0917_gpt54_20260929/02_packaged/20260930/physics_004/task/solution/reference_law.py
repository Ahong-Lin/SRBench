"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'N_P', 'N_D', 'M_damage', 'M_eff_damage']
TARGET = 'dN_P_dt'
PARAMETERS = {'lambda_P': 0.08, 'lambda_D': 0.03, 'k_damage_build': 0.00012, 'k_damage_relax': 0.18, 'alpha_damage': 0.6, 'k_damage_adapt': 0.12}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'N_P', 'N_D', 'M_damage', 'M_eff_damage', 'lambda_P', 'lambda_D', 'k_damage_build', 'k_damage_relax', 'alpha_damage', 'k_damage_adapt', 'dN_P_dt']}
_expression = sympy.sympify('-lambda_P * (1 + alpha_damage * (1 + N_D/(1 + N_D)) * M_eff_damage**2/((1 + M_eff_damage**2) * (1 + M_eff_damage**2/(1 + M_eff_damage**2)))) * N_P', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
