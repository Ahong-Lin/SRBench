Ground truth: dN_P_dt = -lambda_P * (1 + alpha_damage * (1 + N_D/(1 + N_D)) * M_eff_damage**2/((1 + M_eff_damage**2) * (1 + M_eff_damage**2/(1 + M_eff_damage**2)))) * N_P

Fixed parameters: {'lambda_P': 0.08, 'lambda_D': 0.03, 'k_damage_build': 0.00012, 'k_damage_relax': 0.18, 'alpha_damage': 0.6, 'k_damage_adapt': 0.12}
