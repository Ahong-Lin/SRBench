Ground truth: dv_dt = -(phonon_frequency**2 + anharmonic_coefficient*Q**2/(anharmonic_saturation_scale + Q**2))*Q - (damping_rate + amplitude_dependent_damping*y)*v/sqrt(1 + v**2/velocity_damping_saturation_scale)

Fixed parameters: {'phonon_frequency': 2.0, 'damping_rate': 0.2, 'anharmonic_coefficient': 1.2, 'amplitude_dependent_damping': 0.5, 'damping_saturation_scale': 0.3, 'anharmonic_saturation_scale': 0.4, 'damping_relaxation_time': 0.8, 'velocity_damping_saturation_scale': 0.5}
