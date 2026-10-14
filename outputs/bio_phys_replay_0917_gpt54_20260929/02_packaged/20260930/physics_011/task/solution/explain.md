Ground truth: dv_dt = -g - (wake_drag * regime_occupancy / mass) * (v - local_flow_velocity) * Abs(v - local_flow_velocity) * (1 + drag_shape_fraction * Abs(v - local_flow_velocity) / (critical_speed + Abs(v - local_flow_velocity)))

Fixed parameters: {'g': 9.81, 'drag_coefficient': 0.2, 'mass': 1.0, 'wake_relaxation_time': 0.8, 'regime_relaxation_time': 1.2, 'critical_speed': 8.0, 'drag_reduction_fraction': 0.5, 'drag_shape_fraction': 0.8, 'flow_relaxation_time': 1.5, 'entrainment_fraction': 0.35}
