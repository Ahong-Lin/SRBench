Ground truth: dI_dt = beta*S*I/((S + I + R)*(1 + alpha*I/(S + I + R))) - gamma*I*(1 + alpha*I/((S + I + R) + alpha*I + alpha**2*I**2/(S + I + R)))

Fixed parameters: {'gamma': 0.2, 'alpha': 20.0, 'kappa': 0.08, 'beta_floor': 0.35}
