"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['L', 'R_tot', 'E']
TARGET = 'A'
PARAMETERS = {'K_d': 1.0, 'k_activation': 0.9, 'k_deactivation': 0.7, 'alpha_R': 0.4, 'beta_cluster': 0.7, 'k_crowding': 0.35, 'gamma_env': 0.25, 'eta_hetero': 0.6, 'delta_cluster': 1.2}
_symbols = {name: sympy.Symbol(name) for name in ['L', 'R_tot', 'E', 'K_d', 'k_activation', 'k_deactivation', 'alpha_R', 'beta_cluster', 'k_crowding', 'gamma_env', 'eta_hetero', 'delta_cluster', 'A']}
_expression = sympy.sympify('(k_activation*(1 + gamma_env*E*alpha_R*R_tot)*(((1 - eta_hetero*(alpha_R*R_tot)/(1 + alpha_R*R_tot))*L**(1 + beta_cluster*alpha_R*R_tot))/((K_d*(1 + alpha_R*R_tot))**(1 + beta_cluster*alpha_R*R_tot) + L**(1 + beta_cluster*alpha_R*R_tot)) + (eta_hetero*(alpha_R*R_tot)/(1 + alpha_R*R_tot))*L**(1 + beta_cluster*alpha_R*R_tot + delta_cluster)/(K_d**(1 + beta_cluster*alpha_R*R_tot + delta_cluster) + L**(1 + beta_cluster*alpha_R*R_tot + delta_cluster))))/(k_activation + k_deactivation + k_crowding*alpha_R*R_tot)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
