"""Exact ground truth. Private Harbor oracle solution."""
import sympy

FEATURES = ['t', 'P_a', 'H', 'P_v', 'R_v']
TARGET = 'dP_a_dt'
PARAMETERS = {'stroke_volume': 70.0, 'seconds_per_minute': 60.0, 'systemic_vascular_resistance': 1.2, 'arterial_compliance': 1.6, 'resting_heart_rate': 70.0, 'pressure_set_point': 100.0, 'baroreflex_pressure_sensitivity': 0.03, 'heart_rate_adjustment_time': 3.5, 'arterial_stiffening_gain': 3.0, 'arterial_stiffening_pressure_scale': 80.0, 'baroreflex_saturation_pressure_scale': 25.0, 'viscoelastic_relaxation_time': 5.0, 'viscoelastic_buffering_gain': 1.0, 'viscoelastic_pressure_scale': 15.0, 'vascular_resistance_adjustment_time': 8.0, 'reflex_resistance_gain': 1.2}
_symbols = {name: sympy.Symbol(name) for name in ['t', 'P_a', 'H', 'P_v', 'R_v', 'stroke_volume', 'seconds_per_minute', 'systemic_vascular_resistance', 'arterial_compliance', 'resting_heart_rate', 'pressure_set_point', 'baroreflex_pressure_sensitivity', 'heart_rate_adjustment_time', 'arterial_stiffening_gain', 'arterial_stiffening_pressure_scale', 'baroreflex_saturation_pressure_scale', 'viscoelastic_relaxation_time', 'viscoelastic_buffering_gain', 'viscoelastic_pressure_scale', 'vascular_resistance_adjustment_time', 'reflex_resistance_gain', 'dP_a_dt']}
_expression = sympy.sympify('(stroke_volume*H/(seconds_per_minute*(1 + (H/resting_heart_rate)**2)) - P_a/(systemic_vascular_resistance*(1 + reflex_resistance_gain*R_v/(1 + Abs(R_v)))))/((arterial_compliance/(1 + arterial_stiffening_gain*P_a/(arterial_stiffening_pressure_scale + P_a)))*(1 + viscoelastic_buffering_gain*Abs(P_a - P_v)/(viscoelastic_pressure_scale + Abs(P_a - P_v))))', locals=_symbols)
_arguments = [_symbols[name] for name in FEATURES + list(PARAMETERS)]
_function = sympy.lambdify(_arguments, _expression, modules="numpy")

def law(rows):
    return [{TARGET: float(_function(*[float(row[name]) for name in FEATURES], *PARAMETERS.values()))} for row in rows]
