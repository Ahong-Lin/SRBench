"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'q', 'i', 'T_res', 'T_mem']
TARGET = 'di_dt'
PARAMETERS = {'C': 0.0001, 'L': 0.01, 'R': 8.0, 'alpha_T': 0.1, 'C_th': 5.0, 'tau_th': 0.2, 'beta_C': 0.3, 'gamma_RT': 0.4, 'tau_mem': 0.3, 'k_mem': 0.6, 'eta_mem': 0.5}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'q', 'i', 'T_res', 'T_mem', 'C', 'L', 'R', 'alpha_T', 'C_th', 'tau_th', 'beta_C', 'gamma_RT', 'tau_mem', 'k_mem', 'eta_mem', 'di_dt']}
_expression = sympy.sympify('(q/(C*(1 + beta_C*tanh(alpha_T*T_res))) - R*(1 + tanh(alpha_T*T_res) + gamma_RT*tanh(alpha_T*T_res)**2 + eta_mem*tanh(alpha_T*T_mem)*tanh(alpha_T*T_res))*i)/L', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
