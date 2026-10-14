Ground truth: dN_dt = intrinsic_growth_rate*N*(1 - ((((crowding_sensitivity*N + (2 - crowding_sensitivity)*crowding_memory)/(2*carrying_capacity))*(1 + crowding_threshold_shift_strength*(N - crowding_memory)/carrying_capacity))**crowding_exponent))

Fixed parameters: {'intrinsic_growth_rate': 0.6, 'carrying_capacity': 1000.0, 'crowding_exponent': 2.5, 'crowding_adjustment_rate': 0.12, 'crowding_sensitivity_adjustment_rate': 0.3, 'crowding_mismatch_sensitivity': 1.5, 'crowding_threshold_shift_strength': 1.0}
