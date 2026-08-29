import math

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts X from the discovered mathematical relationship:
    X = exp(-decay_rate * t) * A * cos(omega * t) + offset + scale_I * I_light_prev

    Parameters (fitted from training data):
    - A = 2.31399635 (amplitude of oscillation)
    - omega = 0.22656357 (angular frequency, in radians)
    - offset = 0.0832444 (baseline constant)
    - scale_I = 0.02510373 (sensitivity to previous light intensity)
    - decay_rate = 0.04064513 (exponential decay rate)
    """

    # Fitted parameters
    A = 2.31399635
    omega = 0.22656357
    offset = 0.0832444
    scale_I = 0.02510373
    decay_rate = 0.04064513

    results = []
    for row in input_data:
        t = row['t']
        I_light_prev = row['I_light_prev']

        # Apply the discovered formula
        damping = math.exp(-decay_rate * t)
        X = damping * A * math.cos(omega * t) + offset + scale_I * I_light_prev

        results.append({'X': X})

    return results
