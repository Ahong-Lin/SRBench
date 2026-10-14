Ground truth: dp_dt = colonization_rate*p*(1 - p)*(1 + colonization_density_dependence*p/(1 + colonization_saturation_scale*p))*exp(-colonization_stress_sensitivity*extinction_rate/(1 + colonization_stress_half_saturation*extinction_rate)) - extinction_rate*p

Fixed parameters: {'colonization_rate': 1.2, 'colonization_density_dependence': 0.8, 'colonization_saturation_scale': 2.0, 'extinction_relaxation_rate': 0.8, 'extinction_occupancy_sensitivity': 0.9, 'extinction_feedback_half_saturation': 0.3, 'colonization_stress_sensitivity': 3.0, 'colonization_stress_half_saturation': 5.0}
