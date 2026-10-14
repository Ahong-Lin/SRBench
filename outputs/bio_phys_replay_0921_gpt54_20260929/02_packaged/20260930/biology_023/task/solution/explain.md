Ground truth: v_pH = k_cat*E_total*S/((K_M + S)*(1 + 10**((n_low0 + delta_n_low*S/(K_M + S))*(pKa_low - pH - delta_pKa_low*S/(K_M + S))) + 10**((n_high + delta_n_high*S/(K_M + S))*(pH - pKa_high - delta_pKa_high*S/(K_M + S)))))

Fixed parameters: {'k_cat': 100.0, 'E_total': 0.001, 'K_M': 50.0, 'pKa_low': 6.0, 'pKa_high': 8.5, 'delta_pKa_low': 0.8, 'delta_pKa_high': -0.6, 'n_high': 1.3, 'n_low0': 1.1, 'delta_n_low': 0.8, 'delta_n_high': -0.7}
