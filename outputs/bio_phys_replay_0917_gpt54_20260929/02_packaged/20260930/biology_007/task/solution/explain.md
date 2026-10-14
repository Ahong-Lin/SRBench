Ground truth: dN1_dt = dispersal_rate*N2*propensity*(1 + crowding_sensitivity*N2/(1 + crowding_saturation*(N1 + N2))) - dispersal_rate*N1*(1 + crowding_sensitivity*N1/(1 + crowding_saturation*(N1 + N2)))

Fixed parameters: {'dispersal_rate': 0.003, 'crowding_sensitivity': 2.0, 'crowding_saturation': 0.005, 'adaptation_relaxation_rate': 0.08, 'adaptation_crowding_sensitivity': 1.5, 'adaptation_crowding_saturation': 0.01}
