Ground truth: v1_after = (m1*v1_before + m2*v2_before - m2*collision_efficiency*(1 + reduced_mass_partition_sensitivity*(1 - 4*m1*m2/(m1 + m2)**2)/(1 + 4*m1*m2/(m1 + m2)**2))*(1/(1 + Abs(v1_before - v2_before)/(1 + Abs(v1_before - v2_before)) + (Abs(v1_before - v2_before)/(1 + Abs(v1_before - v2_before)))**2))*(((v1_before - v2_before)/(1 + Abs(v1_before - v2_before)))*(1 + Abs(v1_before - v2_before)/(1 + Abs(v1_before - v2_before)))))/(m1 + m2)

Fixed parameters: {'collision_efficiency': 0.8, 'reduced_mass_partition_sensitivity': 0.5}
