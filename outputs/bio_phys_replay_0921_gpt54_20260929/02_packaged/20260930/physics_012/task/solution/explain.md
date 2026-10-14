Ground truth: dN_D_dt = parent_decay_constant*N_P - daughter_decay_constant*N_D/((1 + N_D/damage_capacity)*(1 + (N_D/damage_capacity)**2)*(1 + daughter_decay_constant/damage_capacity))

Fixed parameters: {'parent_decay_constant': 0.02, 'damage_drive_rate': 0.0004, 'damage_relaxation_rate': 0.03, 'capacity_growth_rate': 0.00015, 'capacity_relaxation_rate': 0.015, 'baseline_damage_capacity': 5000.0}
