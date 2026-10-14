Ground truth: v_instantaneous = k_cat*E_total*S/(K_m*(1 + I/K_i + inhibitor_nonlinearity*(I/K_i)**2) + S + substrate_self_inhibition*(1 + crowding_inhibitor_coupling*(I/K_i)/(1 + I/K_i))**2*S**2/K_m)

Fixed parameters: {'K_m': 1.5, 'K_i': 1.0, 'inhibitor_nonlinearity': 0.6, 'substrate_self_inhibition': 0.25, 'crowding_inhibitor_coupling': 1.5}
