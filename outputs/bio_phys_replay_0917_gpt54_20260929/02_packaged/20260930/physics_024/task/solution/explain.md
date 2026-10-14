Ground truth: di_dt = (-(resistance + resistance_nonlinear_coeff*Abs(i))*i - q/(capacitance*(1 + capacitance_relaxation_time*Abs(i)/sqrt(inductance*small_signal_capacitance))))/(inductance/(1 + Abs(i)/saturation_current_scale))

Fixed parameters: {'inductance': 0.5, 'resistance_nonlinear_coeff': 0.8, 'thermal_resistance_gain': 0.6, 'thermal_capacity': 8.0, 'ambient_resistance': 1.0, 'heating_saturation_power': 0.02, 'saturation_current_scale': 0.08, 'capacitance_relaxation_time': 0.03, 'small_signal_capacitance': 0.001, 'capacitance_field_gain': 0.4, 'capacitance_field_scale': 0.001}
