"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['L', 'C']
TARGET = 'f_bound'
PARAMETERS = {'K_d': 10.0, 'frac_high_affinity': 0.25, 'K_d_low': 200.0, 'hill_n': 1.3, 'weight_exchange_amplitude': 0.35, 'K_context': 80.0, 'cooperativity_context_amplitude': 0.9, 'K_cooperativity_context': 150.0, 'affinity_context_amplitude': 2.0, 'K_affinity_context': 120.0}
_symbols = {name: sympy.Symbol(name) for name in ['L', 'C', 'K_d', 'frac_high_affinity', 'K_d_low', 'hill_n', 'weight_exchange_amplitude', 'K_context', 'cooperativity_context_amplitude', 'K_cooperativity_context', 'affinity_context_amplitude', 'K_affinity_context', 'f_bound']}
_expression = sympy.sympify('(frac_high_affinity + weight_exchange_amplitude*C/(K_context + C)) * L**(hill_n + cooperativity_context_amplitude*C/(K_cooperativity_context + C))/((K_d/(1 + affinity_context_amplitude*C/(K_affinity_context + C)))**(hill_n + cooperativity_context_amplitude*C/(K_cooperativity_context + C)) + L**(hill_n + cooperativity_context_amplitude*C/(K_cooperativity_context + C))) + (1 - (frac_high_affinity + weight_exchange_amplitude*C/(K_context + C))) * L**(hill_n + cooperativity_context_amplitude*C/(K_cooperativity_context + C))/(K_d_low**(hill_n + cooperativity_context_amplitude*C/(K_cooperativity_context + C)) + L**(hill_n + cooperativity_context_amplitude*C/(K_cooperativity_context + C)))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
