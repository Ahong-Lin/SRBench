"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'Q', 'I', 'P_pol', 'P_slow']
TARGET = 'dI_dt'
PARAMETERS = {'capacitance': 0.001, 'inductance': 0.001, 'charge_saturation': 0.002, 'current_saturation': 0.5, 'polarization_relaxation_time': 0.0012, 'polarization_coupling': 0.8, 'polarization_saturation': 0.0007, 'slow_polarization_relaxation_time': 0.004, 'slow_polarization_coupling': 0.4, 'slow_polarization_saturation': 0.00035}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'Q', 'I', 'P_pol', 'P_slow', 'capacitance', 'inductance', 'charge_saturation', 'current_saturation', 'polarization_relaxation_time', 'polarization_coupling', 'polarization_saturation', 'slow_polarization_relaxation_time', 'slow_polarization_coupling', 'slow_polarization_saturation', 'dI_dt']}
_expression = sympy.sympify('-(Q + (polarization_coupling/(1 + (P_pol/polarization_saturation)**2))*P_pol/(1 + (P_pol/polarization_saturation)**2) + (slow_polarization_coupling/(1 + (P_slow/slow_polarization_saturation)**2))*P_slow/(1 + (P_slow/slow_polarization_saturation)**2))/(capacitance*(1 + (Q/charge_saturation)**2)*(inductance*(1 + (I/current_saturation)**2)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
