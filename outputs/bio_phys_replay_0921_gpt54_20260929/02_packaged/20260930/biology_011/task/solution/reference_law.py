"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['A', 'G']
TARGET = 'v_translation'
PARAMETERS = {'v_max': 1.0, 'K_A': 1.0, 'K_G': 1.0, 'n_A': 2.0, 'n_G': 2.0, 'alpha_AG': 2.0, 'beta_AG': 1.5, 'gamma_GA': 2.0, 'delta_nAG': 1.2, 'eta_A2': 1.5, 'K_A2': 2.5}
_symbols = {name: sympy.Symbol(name) for name in ['A', 'G', 'v_max', 'K_A', 'K_G', 'n_A', 'n_G', 'alpha_AG', 'beta_AG', 'gamma_GA', 'delta_nAG', 'eta_A2', 'K_A2', 'v_translation']}
_expression = sympy.sympify('v_max*(A**(n_A*(1 + delta_nAG*G**n_G/(K_G**n_G + G**n_G)))/((K_A/(1 + gamma_GA*G**n_G/(K_G**n_G + G**n_G)))**(n_A*(1 + delta_nAG*G**n_G/(K_G**n_G + G**n_G))) + A**(n_A*(1 + delta_nAG*G**n_G/(K_G**n_G + G**n_G))) + beta_AG*(1 + eta_A2*A**n_A/(K_A2**n_A + A**n_A))*(K_A/(1 + gamma_GA*G**n_G/(K_G**n_G + G**n_G)))**(n_A*(1 + delta_nAG*G**n_G/(K_G**n_G + G**n_G)))/(K_G**n_G + G**n_G)))*(G**n_G/(K_G**n_G + G**n_G + alpha_AG*K_G**n_G/(K_A**n_A + A**n_A)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
