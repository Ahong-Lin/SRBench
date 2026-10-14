"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['D', 'tau', 'q', 'tau_est']
TARGET = 'p_inf'
PARAMETERS = {'beta_inf': 0.08, 'alpha_clump': 0.1, 'gamma_att': 0.2, 'delta_dose_att': 0.05}
_symbols = {name: sympy.Symbol(name) for name in ['D', 'tau', 'q', 'tau_est', 'beta_inf', 'alpha_clump', 'gamma_att', 'delta_dose_att', 'p_inf']}
_expression = sympy.sympify('1 - exp(-beta_inf*q*D*tau*((tau/tau_est)/(1 + tau/tau_est))/((1 + alpha_clump*D)*(1 + gamma_att*tau*(1 + delta_dose_att*D))))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
