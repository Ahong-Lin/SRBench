Ground truth: F = attack_rate*R/(1 + attack_rate*(handling_time*(1 + quality_handling_scale*(1 + quality_attack_coupling*attack_rate)/(1 + resource_quality_half_sat*resource_quality)) + handling_crowding_scale*attack_rate*R/(1 + resource_crowding_half_sat*R))*R)

Fixed parameters: {'handling_time': 0.5, 'handling_crowding_scale': 0.2, 'resource_crowding_half_sat': 0.1, 'quality_handling_scale': 1.0, 'resource_quality_half_sat': 1.0, 'quality_attack_coupling': 1.0}
