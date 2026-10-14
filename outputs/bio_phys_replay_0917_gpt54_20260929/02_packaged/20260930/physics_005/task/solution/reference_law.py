"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['L', 'E_nu', 'theta', 'Delta_m2']
TARGET = 'P_e_mu'
PARAMETERS = {'kappa_osc': 1.0}
_symbols = {name: sympy.Symbol(name) for name in ['L', 'E_nu', 'theta', 'Delta_m2', 'kappa_osc', 'P_e_mu']}
_expression = sympy.sympify('sin(2*theta)**2*(1 - exp(-(kappa_osc*L*Delta_m2/E_nu**2)**2)*cos(2*kappa_osc*L*(sqrt(E_nu**2 + Delta_m2) - E_nu) - (kappa_osc*L*Delta_m2/(E_nu**2 + Delta_m2)**(3/2))**2*kappa_osc*L*(sqrt(E_nu**2 + Delta_m2) - E_nu))*exp(-2*(kappa_osc*L*(sqrt(E_nu**2 + Delta_m2) - E_nu))**2/(1 + (kappa_osc*L*Delta_m2/(E_nu**2 + Delta_m2)**(3/2))**2))/(1 + (kappa_osc*L*Delta_m2/(E_nu**2 + Delta_m2)**(3/2))**2))/2', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
