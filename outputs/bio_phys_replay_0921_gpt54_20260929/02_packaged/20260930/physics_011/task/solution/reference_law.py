"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'Pe', 'u', 'v', 'phi_env']
TARGET = 'dPe_dt'
PARAMETERS = {'Rabi_frequency': 1.0, 'dephasing_rate': 0.25, 'bath_relaxation_rate': 0.18, 'bath_coupling': 0.7}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'Pe', 'u', 'v', 'phi_env', 'Rabi_frequency', 'dephasing_rate', 'bath_relaxation_rate', 'bath_coupling', 'dPe_dt']}
_expression = sympy.sympify('Rabi_frequency*(1 - bath_coupling*phi_env*(1 - Pe)/(dephasing_rate + dephasing_rate*(u**2 + v**2) + bath_coupling*phi_env + bath_coupling*phi_env**2*(1 - Pe)))*v', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
