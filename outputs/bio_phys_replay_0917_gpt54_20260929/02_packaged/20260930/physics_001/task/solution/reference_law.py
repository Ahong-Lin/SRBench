"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['L']
TARGET = 'chi'
PARAMETERS = {'susceptibility_amplitude': 1.2, 'critical_exponent_ratio': 1.75, 'correction_amplitude': -0.28, 'correction_exponent': 0.9, 'subleading_correction_amplitude': 0.18, 'subleading_correction_exponent': 1.8, 'subleading_crossover_size': 20.0, 'subleading_saturation_sharpness': 2.0, 'logarithmic_correction_strength': 0.18, 'leading_logarithmic_amplitude': 0.35, 'leading_logarithmic_strength': 0.22, 'leading_logarithmic_crossover_size': 12.0, 'leading_logarithmic_sharpness': 2.0, 'subleading_logarithmic_running_amplitude': 0.3, 'subleading_running_crossover_size': 48.0, 'subleading_running_sharpness': 2.0}
_symbols = {name: sympy.Symbol(name) for name in ['L', 'susceptibility_amplitude', 'critical_exponent_ratio', 'correction_amplitude', 'correction_exponent', 'subleading_correction_amplitude', 'subleading_correction_exponent', 'subleading_crossover_size', 'subleading_saturation_sharpness', 'logarithmic_correction_strength', 'leading_logarithmic_amplitude', 'leading_logarithmic_strength', 'leading_logarithmic_crossover_size', 'leading_logarithmic_sharpness', 'subleading_logarithmic_running_amplitude', 'subleading_running_crossover_size', 'subleading_running_sharpness', 'chi']}
_expression = sympy.sympify('(susceptibility_amplitude * (1 + leading_logarithmic_amplitude / (1 + leading_logarithmic_strength * log(1 + (L / leading_logarithmic_crossover_size)**leading_logarithmic_sharpness)))) * L**critical_exponent_ratio + correction_amplitude * L**(critical_exponent_ratio - correction_exponent) + (subleading_correction_amplitude / (1 + logarithmic_correction_strength * log(1 + (L / subleading_crossover_size)**subleading_saturation_sharpness))) * L**(critical_exponent_ratio - subleading_correction_exponent) / (1 + subleading_logarithmic_running_amplitude * log(1 + (L / subleading_running_crossover_size)**subleading_running_sharpness))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
