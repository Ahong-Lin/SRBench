Ground truth: G_het = (p_f*(1 - p_m) + (1 - p_f)*p_m) + env_sel*tanh(env*(1 + mismatch_sens*Abs(p_f - p_m)))*exp(-stress_window_curv*(env*(1 + mismatch_sens*Abs(p_f - p_m)))**2)*(p_f*(1 - p_m) + (1 - p_f)*p_m)*(1 - (p_f*(1 - p_m) + (1 - p_f)*p_m))/(1 + crowding_curv*(p_f*(1 - p_m) + (1 - p_f)*p_m))

Fixed parameters: {'env_sel': 0.35, 'mismatch_sens': 1.5, 'crowding_curv': 2.0, 'stress_window_curv': 3.0}
