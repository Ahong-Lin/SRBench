Ground truth: dv_dt = -(spring_stiffness/mass)*x - (damping_coefficient/mass)*(1 + internal_loss_level)*(1 + nonlinear_damping_strength*v**2/(1 + nonlinear_damping_strength*v**2))*v - (cubic_stiffness/mass)*x**3

Fixed parameters: {'mass': 1.0, 'spring_stiffness': 4.0, 'damping_coefficient': 0.25, 'cubic_stiffness': 1.2, 'nonlinear_damping_strength': 0.4, 'loss_drive_rate': 0.35, 'loss_relaxation_rate': 0.12, 'loss_activation_rate': 0.5, 'loss_saturation_scale': 0.8}
