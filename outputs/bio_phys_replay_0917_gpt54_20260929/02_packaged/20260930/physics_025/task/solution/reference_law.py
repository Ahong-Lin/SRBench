"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'v_x', 'v_y', 'radiation_damping_strength', 'magnetic_field_z']
TARGET = 'dv_x_dt'
PARAMETERS = {'particle_charge': 1.0, 'particle_mass': 1.0, 'electric_field_x': 0.35, 'signal_speed': 3.0, 'radiation_field_scale': 0.8, 'radiation_activation_rate': 0.12, 'radiation_relaxation_rate': 0.05, 'radiation_damping_capacity': 2.5, 'magnetic_relaxation_rate': 0.08, 'magnetic_screening_strength': 0.03, 'magnetic_field_equilibrium': 1.0}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'v_x', 'v_y', 'radiation_damping_strength', 'magnetic_field_z', 'particle_charge', 'particle_mass', 'electric_field_x', 'signal_speed', 'radiation_field_scale', 'radiation_activation_rate', 'radiation_relaxation_rate', 'radiation_damping_capacity', 'magnetic_relaxation_rate', 'magnetic_screening_strength', 'magnetic_field_equilibrium', 'dv_x_dt']}
_expression = sympy.sympify('(particle_charge*(1 - v_x**2/signal_speed**2)/(particle_mass*(1 - (v_x**2 + v_y**2)/signal_speed**2)**(3/2)))*(electric_field_x + magnetic_field_z*v_y) - radiation_damping_strength*((electric_field_x + magnetic_field_z*v_y)**2/(1 + ((electric_field_x + magnetic_field_z*v_y)/radiation_field_scale)**2))*v_x', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
