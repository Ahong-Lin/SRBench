"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['M', 'R', 'omega', 'temperature_disk']
TARGET = 'I'
PARAMETERS = {'beta_elastic': 2e-07, 'gamma_nonlinear': 2.0, 'temperature_scale': 300.0, 'beta_thermal_softening': 0.4, 'beta_thermal_nonlinear': 0.6}
_symbols = {name: sympy.Symbol(name) for name in ['M', 'R', 'omega', 'temperature_disk', 'beta_elastic', 'gamma_nonlinear', 'temperature_scale', 'beta_thermal_softening', 'beta_thermal_nonlinear', 'I']}
_expression = sympy.sympify('M*R**2/2*(1 + (beta_elastic*omega**2*R**2*(1 + gamma_nonlinear*(1 + beta_thermal_nonlinear*tanh(temperature_disk/temperature_scale))*beta_elastic*omega**2*R**2) + beta_elastic*beta_thermal_softening*tanh(temperature_disk/temperature_scale)*omega**2*R**2*(1 + gamma_nonlinear*(1 + beta_thermal_nonlinear*tanh(temperature_disk/temperature_scale))*beta_elastic*omega**2*R**2))/(1 + gamma_nonlinear*(1 + beta_thermal_nonlinear*tanh(temperature_disk/temperature_scale))*beta_elastic*omega**2*R**2))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
