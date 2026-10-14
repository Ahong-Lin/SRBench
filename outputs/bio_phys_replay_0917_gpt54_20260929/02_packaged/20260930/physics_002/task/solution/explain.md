Ground truth: dT_A_dt = effective_conductance*(T_B - T_A)/(heat_capacity_A*(1 + contrast_nonlinearity_coeff*(1 + conductance_temp_coeff*(T_A + T_B)/2)*(T_B - T_A)**2))

Fixed parameters: {'heat_capacity_A': 100.0, 'heat_capacity_B': 120.0, 'thermal_conductance': 1.5, 'conductance_temp_coeff': 0.001, 'contrast_nonlinearity_coeff': 5e-05, 'conductance_relaxation_time': 25.0}
