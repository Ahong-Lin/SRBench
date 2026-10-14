"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'L', 'L_max', 'interface_mobility', 'active_interface_fraction']
TARGET = 'dL_dt'
PARAMETERS = {'interfacial_tension': 1.2, 'mobility_relaxation_time': 18.0, 'mobility_floor': 0.35, 'interface_screening_time': 6.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'L', 'L_max', 'interface_mobility', 'active_interface_fraction', 'interfacial_tension', 'mobility_relaxation_time', 'mobility_floor', 'interface_screening_time', 'dL_dt']}
_expression = sympy.sympify('interface_mobility * interfacial_tension * active_interface_fraction / L - interface_mobility * interfacial_tension * active_interface_fraction * L / L_max**2', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
