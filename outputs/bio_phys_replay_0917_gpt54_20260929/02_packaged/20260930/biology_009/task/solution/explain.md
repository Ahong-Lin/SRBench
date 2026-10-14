Ground truth: dp_dt = selection_coefficient*p*(1 - p)*(1 + asymmetry_strength*(1 - p)/(asymmetry_threshold + 1 - p))/(1 + delayed_burden/attenuation_capacity + (delayed_burden/attenuation_capacity)**2)

Fixed parameters: {'selection_decay_rate': 0.6, 'selection_capacity': 0.5, 'occupancy_buildup_rate': 1.2, 'occupancy_relaxation_rate': 0.35, 'attenuation_capacity': 2.0, 'asymmetry_strength': 1.6, 'asymmetry_threshold': 0.3, 'burden_buildup_rate': 1.8, 'burden_relaxation_rate': 0.45, 'burden_half_saturation': 1.5}
