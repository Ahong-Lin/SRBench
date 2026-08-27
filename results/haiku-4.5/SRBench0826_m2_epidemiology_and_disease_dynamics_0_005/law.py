import math


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dI_dt from observed state variables using discovered SIRS model with seasonal forcing.

    The underlying dynamics model:
        dI/dt = β·S·I + β_s·cos(2π·t) + β_c·C + α

    Parameters discovered from training data:
        β ≈ -0.0818 (transmission/recovery combined effect via S·I interaction)
        β_s ≈ 0.0173 (seasonal forcing amplitude)
        β_c ≈ -0.364 (immunity suppression dominates)
        α ≈ 0.0499 (baseline offset)
    """
    # Fitted coefficients from symbolic regression
    beta_si = -0.0818      # S·I interaction (transmission × recovery dynamics)
    beta_seasonal = 0.0173  # cos(2π·t) amplitude (annual seasonality)
    beta_c = -0.364         # C (cumulative immunity) suppression effect
    alpha = 0.0499          # baseline offset

    results = []
    for point in input_data:
        t = point['t']
        S = point['S']
        I = point['I']
        C = point['C']

        # Seasonal forcing: annual cycle (period = 1 year, normalized to t in [0, 10.8])
        seasonal_term = beta_seasonal * math.cos(2 * math.pi * t)

        # Transmission dynamics: bilinear S·I (mass-action kinetics)
        transmission_term = beta_si * S * I

        # Immunity suppression: C represents cumulative immunity/recovered population
        immunity_term = beta_c * C

        # Predicted rate of change
        dI_dt_pred = transmission_term + seasonal_term + immunity_term + alpha

        results.append({'dI_dt': dI_dt_pred})

    return results
