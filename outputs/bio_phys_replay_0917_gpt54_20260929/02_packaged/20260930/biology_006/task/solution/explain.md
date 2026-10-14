Ground truth: dH_dt = prey_growth_rate*H*(1 - H/prey_carrying_capacity) - capture_rate*H**2*A/((half_saturation_prey + H + consumer_interference_rate*A)*(half_saturation_prey + H))

Fixed parameters: {'prey_growth_rate': 0.8, 'capture_rate': 1.2, 'conversion_efficiency': 0.18, 'consumer_mortality_rate': 0.25, 'half_saturation_prey': 40.0, 'consumer_interference_rate': 1.5, 'prey_carrying_capacity': 300.0, 'activity_relaxation_rate': 0.6, 'activity_half_saturation_prey': 35.0}
