"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'D', 'recombination_rate', 'occupancy_buffer', 'refractory_occupancy']
TARGET = 'dD_dt'
PARAMETERS = {'recombination_relaxation_rate': 0.8, 'recombination_setpoint': 0.55, 'occupancy_relaxation_rate': 1.2, 'occupancy_sensitivity': 14.0, 'nonlinear_ld_coupling': 8.0, 'boundary_compression_strength': 12.0, 'refractory_occupancy_relaxation_rate': 0.18, 'refractory_occupancy_sensitivity': 20.0, 'refractory_occupancy_strength': 3.0, 'refractory_occupancy_halfscale': 0.5}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'D', 'recombination_rate', 'occupancy_buffer', 'refractory_occupancy', 'recombination_relaxation_rate', 'recombination_setpoint', 'occupancy_relaxation_rate', 'occupancy_sensitivity', 'nonlinear_ld_coupling', 'boundary_compression_strength', 'refractory_occupancy_relaxation_rate', 'refractory_occupancy_sensitivity', 'refractory_occupancy_strength', 'refractory_occupancy_halfscale', 'dD_dt']}
_expression = sympy.sympify('-recombination_rate*D*(1 + nonlinear_ld_coupling*D**2)/(1 + occupancy_buffer + boundary_compression_strength*D**2 + refractory_occupancy_strength*refractory_occupancy/(1 + refractory_occupancy_halfscale + refractory_occupancy))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
