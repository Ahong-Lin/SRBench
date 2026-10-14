"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['L_G', 'Q_G']
TARGET = 'E_G'
PARAMETERS = {'Tm_G': 375.0, 'sigma_G': 180.0, 'flow_sens_G': 0.35, 'sigma_flow_shift_G': 0.4, 'curvature_shape_G': 1.5}
_symbols = {name: sympy.Symbol(name) for name in ['L_G', 'Q_G', 'Tm_G', 'sigma_G', 'flow_sens_G', 'sigma_flow_shift_G', 'curvature_shape_G', 'E_G']}
_expression = sympy.sympify('L_G - Tm_G*(1 - exp(-(L_G/(sigma_G*(1 - sigma_flow_shift_G*Q_G)) + curvature_shape_G*(L_G/(sigma_G*(1 - sigma_flow_shift_G*Q_G)))**2)/(1 + curvature_shape_G*(L_G/(sigma_G*(1 - sigma_flow_shift_G*Q_G)))))) + flow_sens_G*Q_G*Tm_G*(1 - exp(-(L_G/(sigma_G*(1 - sigma_flow_shift_G*Q_G)) + curvature_shape_G*(L_G/(sigma_G*(1 - sigma_flow_shift_G*Q_G)))**2)/(1 + curvature_shape_G*(L_G/(sigma_G*(1 - sigma_flow_shift_G*Q_G))))))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
