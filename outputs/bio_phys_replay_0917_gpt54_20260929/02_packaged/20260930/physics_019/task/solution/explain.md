Ground truth: v_orbit = sqrt((G*M/r)/(1 - 3*G*M/r)*(1 + oblateness_coeff*(R_body**2/r**2)/(1 + R_body**2/r**2) + higher_multipole_coeff*R_body**4/r**4) - frame_drag_coeff*spin_rate*sqrt(G*M/r)*R_body**2/r**2/(1 - 3*G*M/r))

Fixed parameters: {'G': 0.001, 'oblateness_coeff': 0.35, 'frame_drag_coeff': 0.6, 'higher_multipole_coeff': 0.25}
