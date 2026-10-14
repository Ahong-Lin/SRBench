Ground truth: dsigma_dt = hbar*b*(1 + ((shape_mode + stress_memory)/sigma**2)*(1 + Abs(b)*Abs(shape_mode + stress_memory)/sigma**2)/(1 + Abs(shape_mode + stress_memory)/sigma**2 + (shape_mode + stress_memory)**2/sigma**4 + b**2*(shape_mode + stress_memory)**2/sigma**4))/(2*particle_mass*sigma)

Fixed parameters: {'hbar': 1.0, 'particle_mass': 1.0, 'stress_relaxation_rate': 1.5, 'stress_drive_gain': 1.2}
