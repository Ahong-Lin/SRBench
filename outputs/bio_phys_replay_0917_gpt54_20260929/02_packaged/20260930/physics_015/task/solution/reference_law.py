"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'x', 'y', 'z', 'g']
TARGET = 'dz_dt'
PARAMETERS = {'coupling_strength': 1.2, 'detuning': 0.8, 'saturation_strength': 0.4, 'dressing_relaxation_rate': 0.35, 'dressing_strength': 0.6}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'x', 'y', 'z', 'g', 'coupling_strength', 'detuning', 'saturation_strength', 'dressing_relaxation_rate', 'dressing_strength', 'dz_dt']}
_expression = sympy.sympify('g*(1 - (saturation_strength*(x**2 + y**2 + z**2) + saturation_strength**2*(x**2 + y**2 + z**2)**2)/(1 + saturation_strength*(x**2 + y**2 + z**2) + saturation_strength**2*(x**2 + y**2 + z**2)**2))*y', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
