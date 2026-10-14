Ground truth: dI_dt = beta*C*S*I/((S + I + R)*(1 + alpha_sus*(1 - S/(S + I + R))*(1 + R/(S + I + R + alpha_sus)))) - gamma*I - kappa*R*S*I/((S + I + R)*(S + I + R + R))

Fixed parameters: {'beta': 1.2, 'gamma': 0.25, 'kappa': 0.4, 'rho': 0.08, 'alpha_sus': 4.0}
