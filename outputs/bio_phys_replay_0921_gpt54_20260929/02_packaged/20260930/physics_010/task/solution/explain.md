Ground truth: En = Piecewise((V0 - hbar**2*n**2*pi**2/(2*m*L**2) - V0*hbar**2*n**2*pi**2/(12*m*L**2*(V0 + hbar**2*n**2*pi**2/(2*m*L**2))), L*sqrt(2*m*V0)/hbar >= n*pi), (V0 - hbar**2*n**2*pi**2/(2*m*L**2) + hbar**2/L**2*(sqrt(2*m*V0)*L/hbar - n*pi)*tanh(sqrt(2*m*V0)*L/hbar - n*pi) - V0*hbar**2*n**2*pi**2/(12*m*L**2*(V0 + hbar**2*n**2*pi**2/(2*m*L**2))), True))

Fixed parameters: {'hbar': 1.0}
