Ground truth: dI_dt = progression_rate*E - removal_rate*(1 + (infectious_maturation**2/(1 + infectious_maturation**2))*(1 - E/(E + progression_feedback_scale)))*I

Fixed parameters: {'removal_rate': 0.6, 'progression_relaxation_rate': 0.8, 'progression_feedback_scale': 0.25, 'infectious_maturation_rate': 1.2}
