"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['r', 'M_c', 'J2', 'c']
TARGET = 'T'
PARAMETERS = {'G': 6.6743e-11, 'R_eq': 6378000.0}
_symbols = {name: sympy.Symbol(name) for name in ['r', 'M_c', 'J2', 'c', 'G', 'R_eq', 'T']}
_expression = sympy.sympify('2*pi*sqrt(r**3/(G*M_c*(1 - 3*J2*(R_eq/r)**2 + 3*J2*(R_eq/r)**2*(G*M_c/(r*c**2)))))*(1 - 3*G*M_c/(r*c**2))**(-1/2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
