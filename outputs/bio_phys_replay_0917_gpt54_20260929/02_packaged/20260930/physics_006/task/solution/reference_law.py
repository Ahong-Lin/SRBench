"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['q', 'g', 'Lambda_ff', 'm_med']
TARGET = 'dsigma_dq2'
PARAMETERS = {}
_symbols = {name: sympy.Symbol(name) for name in ['q', 'g', 'Lambda_ff', 'm_med', 'dsigma_dq2']}
_expression = sympy.sympify('g**4*exp(-q**2/Lambda_ff**2)/(16*pi*(q**2 + m_med**2)**2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
