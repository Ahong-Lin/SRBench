"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['Q', 'R', 'mu', 'L']
TARGET = 'Delta_p'
PARAMETERS = {'n': 0.8, 'beta_slip': 0.5, 'gamma_slip_sat': 0.4, 'kappa_confine_sat': 2.0, 'lambda_confine_sat': 0.02, 'eta_confine_weaken': 3.0}
_symbols = {name: sympy.Symbol(name) for name in ['Q', 'R', 'mu', 'L', 'n', 'beta_slip', 'gamma_slip_sat', 'kappa_confine_sat', 'lambda_confine_sat', 'eta_confine_weaken', 'Delta_p']}
_expression = sympy.sympify('2*L*mu*(3*Q/(pi*R**3))**n/(R*(1 + beta_slip*mu*(3*Q/(pi*R**3))**n/((1 + eta_confine_weaken*lambda_confine_sat*(3*Q/(pi*R**3))**n)*(1 + gamma_slip_sat*mu*(3*Q/(pi*R**3))**n*(1 + kappa_confine_sat*(3*Q/(pi*R**3))**n/(1 + lambda_confine_sat*(3*Q/(pi*R**3))**n))))))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
