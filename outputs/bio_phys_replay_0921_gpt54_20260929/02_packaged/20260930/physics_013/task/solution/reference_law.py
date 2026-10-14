"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['E', 'theta', 'Z', 'Q2']
TARGET = 'dsigma_dOmega'
PARAMETERS = {'projectile_charge_number': 1.0, 'alpha_em': 0.00729735257, 'hbar_c': 0.1973269804, 'vacuum_polarization_strength': 0.01, 'Q2_scale_reference': 1.0, 'recoil_mass_scale': 5.0, 'nuclear_charge_radius_scale': 2.0}
_symbols = {name: sympy.Symbol(name) for name in ['E', 'theta', 'Z', 'Q2', 'projectile_charge_number', 'alpha_em', 'hbar_c', 'vacuum_polarization_strength', 'Q2_scale_reference', 'recoil_mass_scale', 'nuclear_charge_radius_scale', 'dsigma_dOmega']}
_expression = sympy.sympify('(projectile_charge_number**2 * Z**2 * alpha_em**2 * hbar_c**2 * cos(theta/2)**2 / (1 + Q2 * nuclear_charge_radius_scale**2 / 12)**4) / (4 * E**2 * sin(theta/2)**4 * (1 - vacuum_polarization_strength * log(Q2_scale_reference / (Q2*(1 + Q2/(4 * recoil_mass_scale**2)) / (1 + Q2/(4 * recoil_mass_scale**2)))))**2 * (1 + (Q2*(1 + Q2/(4 * recoil_mass_scale**2)) / (1 + Q2/(4 * recoil_mass_scale**2)))/(4 * recoil_mass_scale**2))**2)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
