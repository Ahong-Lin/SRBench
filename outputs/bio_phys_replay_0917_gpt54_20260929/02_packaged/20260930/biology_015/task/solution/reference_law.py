"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['P_CO2', 'P_O2']
TARGET = 'V_E'
PARAMETERS = {'V_E_max': 80.0, 'D_baseline': 0.12, 'G_CO2': 0.9, 'P_CO2_ref': 40.0, 'G_hypoxia': 1.4, 'P_O2_half': 60.0, 'S_O2': 10.0, 'n_motor': 2.2, 'K_CO2_hypoxia': 1.8, 'Delta_P_O2_half_CO2': -12.0, 'alpha_hypoxia': 2.5, 'K_CO2_compression': 1.3, 'Delta_P_O2_half_potentiation': -10.0}
_symbols = {name: sympy.Symbol(name) for name in ['P_CO2', 'P_O2', 'V_E_max', 'D_baseline', 'G_CO2', 'P_CO2_ref', 'G_hypoxia', 'P_O2_half', 'S_O2', 'n_motor', 'K_CO2_hypoxia', 'Delta_P_O2_half_CO2', 'alpha_hypoxia', 'K_CO2_compression', 'Delta_P_O2_half_potentiation', 'V_E']}
_expression = sympy.sympify('V_E_max*(D_baseline + G_CO2*(1 + K_CO2_hypoxia*(1 - (1 - 1/(1 + exp((P_O2 - ((P_O2_half + Delta_P_O2_half_CO2*(P_CO2/P_CO2_ref - 1)) + Delta_P_O2_half_potentiation))/S_O2)))**alpha_hypoxia))*(P_CO2/P_CO2_ref)/(1 + K_CO2_compression*(P_CO2/P_CO2_ref - 1)) + G_hypoxia*(1 - (1 - 1/(1 + exp((P_O2 - (P_O2_half + Delta_P_O2_half_CO2*(P_CO2/P_CO2_ref - 1)))/S_O2)))**alpha_hypoxia))**n_motor/(1 + (D_baseline + G_CO2*(1 + K_CO2_hypoxia*(1 - (1 - 1/(1 + exp((P_O2 - ((P_O2_half + Delta_P_O2_half_CO2*(P_CO2/P_CO2_ref - 1)) + Delta_P_O2_half_potentiation))/S_O2)))**alpha_hypoxia))*(P_CO2/P_CO2_ref)/(1 + K_CO2_compression*(P_CO2/P_CO2_ref - 1)) + G_hypoxia*(1 - (1 - 1/(1 + exp((P_O2 - (P_O2_half + Delta_P_O2_half_CO2*(P_CO2/P_CO2_ref - 1)))/S_O2)))**alpha_hypoxia))**n_motor)', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
