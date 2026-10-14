Ground truth: dv_dt = -((spring_constant * (1 + (cubic_stiffness_coefficient * z**2) / (1 + saturation_strain_coefficient * z**2))) / mass) * z - (damping_coefficient / mass) * v - (nonlinear_drag_coefficient / mass) * Abs(v) * v

Fixed parameters: {'mass': 1.0, 'spring_constant': 12.0, 'damping_coefficient': 0.8, 'cubic_stiffness_coefficient': 1.5, 'nonlinear_drag_coefficient': 0.25, 'relaxation_time': 0.7, 'conditioning_rate': 0.9, 'conditioning_strain_coefficient': 0.6, 'saturation_strain_coefficient': 0.8}
