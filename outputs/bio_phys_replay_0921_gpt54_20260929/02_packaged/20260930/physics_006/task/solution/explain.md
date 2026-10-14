Ground truth: dV_C_dt = -V_C/(capacitance*(1 + cap_temp_coeff*(T_C - T_ref))*(1 + cap_voltage_coeff*V_C**2)*resistance*(1 + temp_coeff*(T_R - T_ref) + resistance_temp_quadratic_coeff*(T_R - T_ref)**2))

Fixed parameters: {'resistance': 50.0, 'capacitance': 0.01, 'temp_coeff': 0.004, 'cap_temp_coeff': 0.0005, 'thermal_capacitance': 0.2, 'thermal_resistance': 8.0, 'T_ref': 300.0, 'T_ambient': 300.0, 'resistance_temp_quadratic_coeff': 1e-06, 'cap_thermal_capacitance': 1.5, 'cap_thermal_resistance': 20.0, 'resistor_to_cap_thermal_resistance': 6.0, 'cap_voltage_coeff': 0.002}
