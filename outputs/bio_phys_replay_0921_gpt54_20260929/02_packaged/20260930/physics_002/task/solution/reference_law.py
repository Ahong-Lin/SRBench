"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'eta', 'u', 'gravity_acceleration', 'compressibility_strain']
TARGET = 'deta_dt'
PARAMETERS = {'mode_wavenumber': 2.5, 'fluid_depth': 0.8, 'gravity_relaxation_rate': 0.15, 'gravity_reference': 9.81, 'compressibility_relaxation_rate': 1.2, 'compressibility_coupling': 0.02}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'eta', 'u', 'gravity_acceleration', 'compressibility_strain', 'mode_wavenumber', 'fluid_depth', 'gravity_relaxation_rate', 'gravity_reference', 'compressibility_relaxation_rate', 'compressibility_coupling', 'deta_dt']}
_expression = sympy.sympify('u/((1 + (mode_wavenumber*eta)**2)*(1 + compressibility_strain))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
