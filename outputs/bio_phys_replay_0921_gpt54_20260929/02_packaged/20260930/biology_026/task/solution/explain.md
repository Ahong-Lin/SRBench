Ground truth: E_G = L_G - Tm_G*(1 - exp(-(L_G/(sigma_G*(1 - sigma_flow_shift_G*Q_G)) + curvature_shape_G*(L_G/(sigma_G*(1 - sigma_flow_shift_G*Q_G)))**2)/(1 + curvature_shape_G*(L_G/(sigma_G*(1 - sigma_flow_shift_G*Q_G)))))) + flow_sens_G*Q_G*Tm_G*(1 - exp(-(L_G/(sigma_G*(1 - sigma_flow_shift_G*Q_G)) + curvature_shape_G*(L_G/(sigma_G*(1 - sigma_flow_shift_G*Q_G)))**2)/(1 + curvature_shape_G*(L_G/(sigma_G*(1 - sigma_flow_shift_G*Q_G))))))

Fixed parameters: {'Tm_G': 375.0, 'sigma_G': 180.0, 'flow_sens_G': 0.35, 'sigma_flow_shift_G': 0.4, 'curvature_shape_G': 1.5}
