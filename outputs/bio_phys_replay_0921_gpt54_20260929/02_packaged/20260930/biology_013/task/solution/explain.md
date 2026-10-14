Ground truth: dI_dt = transmission_rate*S/(susceptible_saturation*(1 + transmission_burden_gain*B/(removal_burden_saturation + B)) + S)*I/(infectious_saturation + I) - removal_rate*(1 + removal_burden_gain*B/(removal_burden_saturation + B))*I

Fixed parameters: {'transmission_rate': 2.2, 'removal_rate': 0.5, 'susceptible_saturation': 0.25, 'removal_burden_gain': 1.2, 'removal_burden_saturation': 0.08, 'burden_adjustment_rate': 1.0, 'transmission_burden_gain': 1.0, 'infectious_saturation': 0.08}
