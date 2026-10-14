"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'Ih', 'Iv', 'host_transmission_rate', 'host_exposure_memory']
TARGET = 'dIh_dt'
PARAMETERS = {'vector_transmission_rate': 0.9, 'host_susceptible_background': 1.0, 'vector_susceptible_background': 1.1, 'host_removal_rate': 0.25, 'vector_removal_rate': 0.3, 'host_infection_capacity': 1.0, 'vector_infection_capacity': 1.0, 'vector_to_host_saturation_scale': 0.15, 'infected_host_crowding_saturation_strength': 2.0, 'host_transmission_rate_relaxation_rate': 0.2, 'host_transmission_rate_feedback_strength': 0.8, 'host_transmission_rate_baseline': 0.9, 'host_exposure_memory_relaxation_rate': 0.6, 'host_exposure_memory_accumulation_rate': 1.2, 'host_exposure_memory_strength': 1.5}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'Ih', 'Iv', 'host_transmission_rate', 'host_exposure_memory', 'vector_transmission_rate', 'host_susceptible_background', 'vector_susceptible_background', 'host_removal_rate', 'vector_removal_rate', 'host_infection_capacity', 'vector_infection_capacity', 'vector_to_host_saturation_scale', 'infected_host_crowding_saturation_strength', 'host_transmission_rate_relaxation_rate', 'host_transmission_rate_feedback_strength', 'host_transmission_rate_baseline', 'host_exposure_memory_relaxation_rate', 'host_exposure_memory_accumulation_rate', 'host_exposure_memory_strength', 'dIh_dt']}
_expression = sympy.sympify('host_transmission_rate * host_susceptible_background * (Iv / (1 + Iv / (vector_to_host_saturation_scale * (1 - Ih / host_infection_capacity) / ((1 + infected_host_crowding_saturation_strength * Ih / host_infection_capacity) * (1 + host_exposure_memory_strength * host_exposure_memory))))) * (1 - Ih / host_infection_capacity) - host_removal_rate * Ih', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
