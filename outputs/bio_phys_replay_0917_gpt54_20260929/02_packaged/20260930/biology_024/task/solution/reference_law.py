"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'N_c', 'N_n', 'A']
TARGET = 'dN_n_dt'
PARAMETERS = {'k_import': 0.05, 'k_export': 0.03, 'k_bind_import': 0.0001, 'k_unbind_import': 0.2, 'K_import_sat': 5000.0, 'K_export_sat': 5000.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'N_c', 'N_n', 'A', 'k_import', 'k_export', 'k_bind_import', 'k_unbind_import', 'K_import_sat', 'K_export_sat', 'dN_n_dt']}
_expression = sympy.sympify('k_import * A * N_c / (1 + N_c / K_import_sat) - k_export * A * N_n / (1 + N_n / (K_export_sat * A**2))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
