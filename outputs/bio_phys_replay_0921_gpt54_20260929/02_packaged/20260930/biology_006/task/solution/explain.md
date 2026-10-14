Ground truth: dx_dt = (1 - x)/(recovery_time_constant*(1 + replenishment_fatigue)) - presynaptic_rate*(1 - release_site_occupancy)*u*x**2/((1 + replenishment_fatigue)*(1 + baseline_utilization*replenishment_fatigue))

Fixed parameters: {'recovery_time_constant': 0.8, 'facilitation_time_constant': 0.2, 'presynaptic_rate': 15.0, 'baseline_utilization': 0.25, 'fatigue_build_time_constant': 0.5, 'fatigue_recovery_time_constant': 1.2, 'release_site_reset_time_constant': 0.05}
