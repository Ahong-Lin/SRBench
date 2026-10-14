"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'sigma', 'b', 'shape_mode', 'stress_memory']
TARGET = 'dsigma_dt'
PARAMETERS = {'hbar': 1.0, 'particle_mass': 1.0, 'stress_relaxation_rate': 1.5, 'stress_drive_gain': 1.2}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'sigma', 'b', 'shape_mode', 'stress_memory', 'hbar', 'particle_mass', 'stress_relaxation_rate', 'stress_drive_gain', 'dsigma_dt']}
_expression = sympy.sympify('hbar*b*(1 + ((shape_mode + stress_memory)/sigma**2)*(1 + Abs(b)*Abs(shape_mode + stress_memory)/sigma**2)/(1 + Abs(shape_mode + stress_memory)/sigma**2 + (shape_mode + stress_memory)**2/sigma**4 + b**2*(shape_mode + stress_memory)**2/sigma**4))/(2*particle_mass*sigma)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
