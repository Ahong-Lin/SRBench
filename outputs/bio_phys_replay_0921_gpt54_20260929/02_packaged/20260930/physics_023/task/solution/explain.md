Ground truth: k = nu*exp(-(DeltaF - S_act*T - C_act*T**2*(1 + DeltaF/(DeltaF + DeltaF_soft))/(T + T_sat))/T)/(1 + (xi_env/T)*exp(-(C_act*T**2*(1 + DeltaF/(DeltaF + DeltaF_soft))/(T + T_sat))/T))

Fixed parameters: {'S_act': 0.8, 'C_act': 1.5, 'T_sat': 1.0, 'DeltaF_soft': 4.0}
