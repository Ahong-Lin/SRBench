"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['L', 'E_nu', 'theta_mix', 'delta_m2']
TARGET = 'P_transition'
PARAMETERS = {'kappa_osc': 1.27, 'matter_potential_coeff': 0.0006}
_symbols = {name: sympy.Symbol(name) for name in ['L', 'E_nu', 'theta_mix', 'delta_m2', 'kappa_osc', 'matter_potential_coeff', 'P_transition']}
_expression = sympy.sympify('(1 - exp(-pi*kappa_osc*delta_m2*sin(2*theta_mix)**2/(E_nu*(Abs((matter_potential_coeff/(1 + E_nu/kappa_osc))*((1 - exp(-L/kappa_osc)) + sin(L/kappa_osc))/delta_m2)/kappa_osc + 1/kappa_osc))))*(sin(2*theta_mix)**2/(sin(2*theta_mix)**2 + (cos(2*theta_mix) - (matter_potential_coeff/(1 + E_nu/kappa_osc))*((1 - exp(-L/kappa_osc)) + sin(L/kappa_osc))*E_nu/delta_m2)**2))*sin(kappa_osc*delta_m2*L*sqrt(sin(2*theta_mix)**2 + (cos(2*theta_mix) - (matter_potential_coeff/(1 + E_nu/kappa_osc))*((1 - exp(-L/kappa_osc)) + sin(L/kappa_osc))*E_nu/delta_m2)**2)/E_nu + sin(L/kappa_osc)*((matter_potential_coeff/(1 + E_nu/kappa_osc))*E_nu/delta_m2))**2 + exp(-pi*kappa_osc*delta_m2*sin(2*theta_mix)**2/(E_nu*(Abs((matter_potential_coeff/(1 + E_nu/kappa_osc))*((1 - exp(-L/kappa_osc)) + sin(L/kappa_osc))/delta_m2)/kappa_osc + 1/kappa_osc)))*(sin(2*theta_mix)**2/(sin(2*theta_mix)**2 + (cos(2*theta_mix) - (matter_potential_coeff/(1 + E_nu/kappa_osc))*((1 - exp(-L/kappa_osc)) + sin(L/kappa_osc))*E_nu/delta_m2)**2))*sin(kappa_osc*delta_m2*L*sqrt(sin(2*theta_mix)**2 + (cos(2*theta_mix) - (matter_potential_coeff/(1 + E_nu/kappa_osc))*((1 - exp(-L/kappa_osc)) + sin(L/kappa_osc))*E_nu/delta_m2)**2)/E_nu + sin(L/kappa_osc)*((matter_potential_coeff/(1 + E_nu/kappa_osc))*E_nu/delta_m2) + pi/2)**2', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
