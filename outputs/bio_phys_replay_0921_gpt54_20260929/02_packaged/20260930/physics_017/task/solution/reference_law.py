"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['T', 'v_s', 'v_l', 'Theta_a']
TARGET = 'C_v'
PARAMETERS = {'k_B': 1.380649e-23, 'hbar': 1.054571817e-34, 'alpha_nd': 1.2, 'beta_nd': 0.8, 'gamma_lv': 0.6, 'eta_aniso': 1.0}
_symbols = {name: sympy.Symbol(name) for name in ['T', 'v_s', 'v_l', 'Theta_a', 'k_B', 'hbar', 'alpha_nd', 'beta_nd', 'gamma_lv', 'eta_aniso', 'C_v']}
_expression = sympy.sympify('2*pi**2*k_B**4*T**3/(15*hbar**3)*(1/(v_l**3*(1 + (T/(Theta_a*(1 + gamma_lv*(1 - v_s/v_l))))**2*(v_s/v_l)**2 + beta_nd*(1 + eta_aniso*(1 - v_s/v_l)**2)*(T/(Theta_a*(1 + gamma_lv*(1 - v_s/v_l))))**4*(v_s/v_l)**4)) + 2/(v_s**3*(1 + (T/Theta_a)**2 + alpha_nd*(1 + eta_aniso*(1 - v_s/v_l)**2)*(T/Theta_a)**4)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
