Ground truth: dP_dt = k_cat*C/(1 + (P/(K_I_cat*(1 + S/K_S_protect)))**n_I_cat) - k_on_P*(E_total - C - EP)*P/(1 + P/K_I_P) + k_off_P*EP

Fixed parameters: {'E_total': 1.0, 'k_on': 0.08, 'k_off': 1.2, 'k_cat': 2.0, 'k_on_P': 0.05, 'k_off_P': 0.2, 'K_I_P': 30.0, 'K_I_cat': 40.0, 'n_I_cat': 2.0, 'K_S_protect': 50.0}
