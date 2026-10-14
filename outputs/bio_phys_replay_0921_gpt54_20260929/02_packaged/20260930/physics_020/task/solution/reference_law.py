"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['x', 'confinement_strength']
TARGET = 's_mix'
PARAMETERS = {'accessibility_scale': 12.0, 'cooperative_accessibility': 8.0, 'heterogeneity_weight': 6.0}
_symbols = {name: sympy.Symbol(name) for name in ['x', 'confinement_strength', 'accessibility_scale', 'cooperative_accessibility', 'heterogeneity_weight', 's_mix']}
_expression = sympy.sympify('(-x*log(x) - (1 - x)*log(1 - x))/(1 + confinement_strength/(1 + accessibility_scale*(1 + heterogeneity_weight*(x*(1 - x))**2/(1 + cooperative_accessibility*(x*(1 - x))**2))*(x*(1 - x))**2*(1 + cooperative_accessibility*(x*(1 - x))**2)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
