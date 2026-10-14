"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['DeltaF', 'T', 'nu', 'xi_env']
TARGET = 'k'
PARAMETERS = {'S_act': 0.8, 'C_act': 1.5, 'T_sat': 1.0, 'DeltaF_soft': 4.0}
_symbols = {name: sympy.Symbol(name) for name in ['DeltaF', 'T', 'nu', 'xi_env', 'S_act', 'C_act', 'T_sat', 'DeltaF_soft', 'k']}
_expression = sympy.sympify('nu*exp(-(DeltaF - S_act*T - C_act*T**2*(1 + DeltaF/(DeltaF + DeltaF_soft))/(T + T_sat))/T)/(1 + (xi_env/T)*exp(-(C_act*T**2*(1 + DeltaF/(DeltaF + DeltaF_soft))/(T + T_sat))/T))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
