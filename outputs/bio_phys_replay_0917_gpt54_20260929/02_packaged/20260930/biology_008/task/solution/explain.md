Ground truth: dA_dt = maturation_rate*exp(-developmental_stress_sensitivity*D)*J*(J/(J + carrying_capacity))/((1 + (J + A)/carrying_capacity)*(1 + J/carrying_capacity)) - adult_mortality_rate*A - adult_crowding_coefficient*A**2

Fixed parameters: {'fecundity_rate': 1.4, 'carrying_capacity': 500.0, 'maturation_rate': 0.8, 'juvenile_mortality_rate': 0.2, 'adult_mortality_rate': 0.15, 'adult_crowding_coefficient': 0.001, 'stress_accumulation_rate': 1.2, 'stress_recovery_rate': 0.35, 'developmental_stress_sensitivity': 0.6}
