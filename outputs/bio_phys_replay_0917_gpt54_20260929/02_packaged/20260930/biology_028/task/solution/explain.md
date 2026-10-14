Ground truth: dC_dt = progression_rate*C_latent - clearance_rate*C*I_late/((late_half_saturation*(1 + inflow_clearance_modulation*progression_rate*C_latent/(late_half_saturation + progression_rate*C_latent)))*(1 + C/late_half_saturation) + I_late)*(late_half_saturation + C)/(late_half_saturation + 2*C)

Fixed parameters: {'progression_rate': 0.22, 'clearance_rate': 0.32, 'stage_progression_rate': 0.18, 'late_half_saturation': 120.0, 'inflow_clearance_modulation': 3.0}
