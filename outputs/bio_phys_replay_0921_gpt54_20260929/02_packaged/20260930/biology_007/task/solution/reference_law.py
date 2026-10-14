"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'E', 'I', 'S_I', 'A_I']
TARGET = 'dE_dt'
PARAMETERS = {'tau_E': 12.0, 'tau_I': 10.0, 'tau_SI': 24.0, 'tau_AI': 90.0, 'w_EE': 11.0, 'w_EI': 9.0, 'w_IE': 10.0, 'external_drive_E': 1.2, 'external_drive_I': 0.25, 'gain_E': 4.5, 'gain_I': 4.0, 'threshold_E': 2.1, 'threshold_I': 1.4, 'g_IE_delayed': 1.6, 'shunt_SI_E': 1.2, 'threshold_shift_SI_E': 1.5, 'sat_threshold_SI_E': 1.0, 'slow_threshold_mix_E': 0.8, 'coop_inhibitory_E': 0.9}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'E', 'I', 'S_I', 'A_I', 'tau_E', 'tau_I', 'tau_SI', 'tau_AI', 'w_EE', 'w_EI', 'w_IE', 'external_drive_E', 'external_drive_I', 'gain_E', 'gain_I', 'threshold_E', 'threshold_I', 'g_IE_delayed', 'shunt_SI_E', 'threshold_shift_SI_E', 'sat_threshold_SI_E', 'slow_threshold_mix_E', 'coop_inhibitory_E', 'dE_dt']}
_expression = sympy.sympify('((1 - E)/(1 + exp(-(gain_E/(1 + shunt_SI_E*S_I))*(w_EE*E - w_EI*I + external_drive_E - threshold_E - threshold_shift_SI_E*((S_I + slow_threshold_mix_E*A_I)*(1 + coop_inhibitory_E*(S_I + slow_threshold_mix_E*A_I)))/(1 + sat_threshold_SI_E*((S_I + slow_threshold_mix_E*A_I)*(1 + coop_inhibitory_E*(S_I + slow_threshold_mix_E*A_I))))))) - E)/tau_E - g_IE_delayed*S_I*E', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
