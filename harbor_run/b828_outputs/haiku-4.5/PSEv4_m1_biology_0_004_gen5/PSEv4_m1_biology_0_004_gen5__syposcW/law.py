import math

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discovered law: X = exp(-lambda*t) * (A*sin(omega*t + phase1) + B*I_light*sin(2*omega*t + phase2)) + offset

    Parameters fitted from training data:
    - A = 2.1403850412
    - B = -0.2821393786
    - omega = 0.2591650249
    - lambda = 0.0321824487
    - phase1 = 0.7275460645
    - phase2 = -2.4962127502
    - offset = 0.0718672222
    """

    # Fitted parameters
    A = 2.1403850412
    B = -0.2821393786
    omega = 0.2591650249
    lambda_decay = 0.0321824487
    phase1 = 0.7275460645
    phase2 = -2.4962127502
    offset = 0.0718672222

    results = []

    for row in input_data:
        t = row['t']
        I_light_prev = row['I_light_prev']

        # Compute the exponential envelope
        envelope = math.exp(-lambda_decay * t)

        # Compute the oscillation: first harmonic + second harmonic modulated by I_light
        term1 = A * math.sin(omega * t + phase1)
        term2 = B * I_light_prev * math.sin(2 * omega * t + phase2)
        oscillation = term1 + term2

        # Combine: envelope * oscillation + offset
        X = envelope * oscillation + offset

        results.append({'X': X})

    return results
