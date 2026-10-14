Ground truth: di_dt = (q/(C*(1 + beta_C*tanh(alpha_T*T_res))) - R*(1 + tanh(alpha_T*T_res) + gamma_RT*tanh(alpha_T*T_res)**2 + eta_mem*tanh(alpha_T*T_mem)*tanh(alpha_T*T_res))*i)/L

Fixed parameters: {'C': 0.0001, 'L': 0.01, 'R': 8.0, 'alpha_T': 0.1, 'C_th': 5.0, 'tau_th': 0.2, 'beta_C': 0.3, 'gamma_RT': 0.4, 'tau_mem': 0.3, 'k_mem': 0.6, 'eta_mem': 0.5}
