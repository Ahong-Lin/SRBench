"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['Q', 'mu', 'L', 'R']
TARGET = 'delta_p'
PARAMETERS = {'p_c': 50000.0, 'gamma_c': 400000.0}
_symbols = {name: sympy.Symbol(name) for name in ['Q', 'mu', 'L', 'R', 'p_c', 'gamma_c', 'delta_p']}
_expression = sympy.sympify('(8*(mu/(1 + (Q/(mu*R**3))/gamma_c))*L*Q/(pi*R**4) + 8*(mu/(1 + (Q/(mu*R**3))/gamma_c))*L*Q/(pi*R**4)*(Q/((mu/(1 + (Q/(mu*R**3))/gamma_c))*R))/(1 + Q/((mu/(1 + (Q/(mu*R**3))/gamma_c))*R)) + 8*(mu/(1 + (Q/(mu*R**3))/gamma_c))*L*Q/(pi*R**4)*(R/L)*(Q/((mu/(1 + (Q/(mu*R**3))/gamma_c))*R))/(1 + Q/((mu/(1 + (Q/(mu*R**3))/gamma_c))*R)))/(1 + (8*(mu/(1 + (Q/(mu*R**3))/gamma_c))*L*Q/(pi*R**4) + 8*(mu/(1 + (Q/(mu*R**3))/gamma_c))*L*Q/(pi*R**4)*(Q/((mu/(1 + (Q/(mu*R**3))/gamma_c))*R))/(1 + Q/((mu/(1 + (Q/(mu*R**3))/gamma_c))*R)) + 8*(mu/(1 + (Q/(mu*R**3))/gamma_c))*L*Q/(pi*R**4)*(R/L)*(Q/((mu/(1 + (Q/(mu*R**3))/gamma_c))*R))/(1 + Q/((mu/(1 + (Q/(mu*R**3))/gamma_c))*R)))/(8*(mu/(1 + (Q/(mu*R**3))/gamma_c))*L*Q/(pi*R**4) + p_c) + ((8*(mu/(1 + (Q/(mu*R**3))/gamma_c))*L*Q/(pi*R**4) + 8*(mu/(1 + (Q/(mu*R**3))/gamma_c))*L*Q/(pi*R**4)*(Q/((mu/(1 + (Q/(mu*R**3))/gamma_c))*R))/(1 + Q/((mu/(1 + (Q/(mu*R**3))/gamma_c))*R)) + 8*(mu/(1 + (Q/(mu*R**3))/gamma_c))*L*Q/(pi*R**4)*(R/L)*(Q/((mu/(1 + (Q/(mu*R**3))/gamma_c))*R))/(1 + Q/((mu/(1 + (Q/(mu*R**3))/gamma_c))*R)))/(8*(mu/(1 + (Q/(mu*R**3))/gamma_c))*L*Q/(pi*R**4) + p_c))**2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
