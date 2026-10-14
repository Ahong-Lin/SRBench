"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['Q', 'mu', 'L', 'R']
TARGET = 'delta_p'
PARAMETERS = {'Rho': 1000.0, 'laminar_inertia_coeff': 0.08, 'entrance_development_coeff': 0.04, 'shear_thinning_strength': 0.6, 'shear_thinning_exponent': 0.8, 'shear_thinning_saturation_strength': 1.2, 'shear_profile_shape_factor': 2.0}
_symbols = {name: sympy.Symbol(name) for name in ['Q', 'mu', 'L', 'R', 'Rho', 'laminar_inertia_coeff', 'entrance_development_coeff', 'shear_thinning_strength', 'shear_thinning_exponent', 'shear_thinning_saturation_strength', 'shear_profile_shape_factor', 'delta_p']}
_expression = sympy.sympify('8*mu*L*Q/(pi*R**4*(1 + shear_thinning_strength*(4*Q/(pi*R**3)*((shear_profile_shape_factor + 1)/(shear_profile_shape_factor + 2)))**shear_thinning_exponent/(1 + shear_thinning_saturation_strength*(4*Q/(pi*R**3)*((shear_profile_shape_factor + 1)/(shear_profile_shape_factor + 2)))**shear_thinning_exponent)))*(1 + laminar_inertia_coeff*Q*Rho/(pi*mu*R) + entrance_development_coeff*(2*Rho*Q/(pi*mu*R))*(R/L))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
