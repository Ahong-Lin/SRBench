Ground truth: a = Piecewise((0, Abs(F) <= (mu_s + eta*log(1 + m*g/N0))*m*g), ((F - mu_k*m*g*sign(F)/(1 + beta*(1 - exp(-gamma*(1 + delta*log(1 + m*g/N0))*(Abs(F)/(m*g) - (mu_s + eta*log(1 + m*g/N0)))))))/m, True))

Fixed parameters: {'mu_s': 0.35, 'mu_k': 0.25, 'beta': 2.0, 'gamma': 3.0, 'eta': 0.08, 'N0': 10.0, 'delta': 0.5}
