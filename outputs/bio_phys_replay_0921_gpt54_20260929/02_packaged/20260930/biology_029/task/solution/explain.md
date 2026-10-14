Ground truth: dI_dt = transmission_rate*S*I/(1 + saturation_strength*(I + I_phase + phase_curvature_strength*I_phase**2/(1 + late_phase_share_saturation*I_phase))) - recovery_rate*I_phase/(1 + phase_saturation*I_phase)

Fixed parameters: {'transmission_rate': 1.8, 'recovery_rate': 0.6, 'saturation_strength': 8.0, 'phase_progression_rate': 1.2, 'phase_saturation': 4.0, 'phase_curvature_strength': 2.0, 'late_phase_share_saturation': 10.0}
