Ground truth: dP_a_dt = (P_set + autonomic_pressure_gain*w*(1 + (pressure_efficacy_error_gain*(P_set - P_a))/(1 + Abs(pressure_efficacy_error_gain*(P_set - P_a)))) - P_a)/pressure_time_constant

Fixed parameters: {'P_set': 100.0, 'u_baseline': 0.5, 'autonomic_pressure_gain': 28.0, 'pressure_time_constant': 5.0, 'autonomic_time_constant': 3.0, 'baroreflex_sensitivity': 0.08, 'pressure_efficacy_error_gain': 0.03, 'slow_support_weight': 0.6, 'slow_autonomic_time_constant': 12.0, 'hemodynamic_transduction_time_constant': 4.0}
