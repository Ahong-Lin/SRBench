"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'Q', 'v', 'y']
TARGET = 'dv_dt'
PARAMETERS = {'phonon_frequency': 2.0, 'damping_rate': 0.2, 'anharmonic_coefficient': 1.2, 'amplitude_dependent_damping': 0.5, 'damping_saturation_scale': 0.3, 'anharmonic_saturation_scale': 0.4, 'damping_relaxation_time': 0.8, 'velocity_damping_saturation_scale': 0.5}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'Q', 'v', 'y', 'phonon_frequency', 'damping_rate', 'anharmonic_coefficient', 'amplitude_dependent_damping', 'damping_saturation_scale', 'anharmonic_saturation_scale', 'damping_relaxation_time', 'velocity_damping_saturation_scale', 'dv_dt']}
_expression = sympy.sympify('-(phonon_frequency**2 + anharmonic_coefficient*Q**2/(anharmonic_saturation_scale + Q**2))*Q - (damping_rate + amplitude_dependent_damping*y)*v/sqrt(1 + v**2/velocity_damping_saturation_scale)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
