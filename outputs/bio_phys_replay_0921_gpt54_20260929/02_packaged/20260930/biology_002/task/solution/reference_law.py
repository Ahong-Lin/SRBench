"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['H0', 'Ne', 'g', 'mu']
TARGET = 'H_g'
PARAMETERS = {'sigma': 0.3}
_symbols = {name: sympy.Symbol(name) for name in ['H0', 'Ne', 'g', 'mu', 'sigma', 'H_g']}
_expression = sympy.sympify('2*mu*(1 - mu)/(1 - (1 - 1/(2*Ne*(1 + g/(2*Ne))))*(1 - 2*mu)^2 + sigma*(1 - 2*mu)^2*mu*(1 - mu)/((1 + 2*Ne)*(1 + g/(2*Ne)))) + (H0 - 2*mu*(1 - mu)/(1 - (1 - 1/(2*Ne*(1 + g/(2*Ne))))*(1 - 2*mu)^2 + sigma*(1 - 2*mu)^2*mu*(1 - mu)/((1 + 2*Ne)*(1 + g/(2*Ne)))))/(((2*mu*(1 - mu)/(H0*(1 - (1 - 1/(2*Ne*(1 + g/(2*Ne))))*(1 - 2*mu)^2 + sigma*(1 - 2*mu)^2*mu*(1 - mu)/((1 + 2*Ne)*(1 + g/(2*Ne))))) - 1)*exp(g*(1 - (1 - 1/(2*Ne*(1 + g/(2*Ne))))*(1 - 2*mu)^2 + sigma*(1 - 2*mu)^2*mu*(1 - mu)/((1 + 2*Ne)*(1 + g/(2*Ne))))) + 1))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
