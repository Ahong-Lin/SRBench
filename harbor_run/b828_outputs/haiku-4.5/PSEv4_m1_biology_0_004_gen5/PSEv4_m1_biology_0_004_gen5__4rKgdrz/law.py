import numpy as np

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Computes X from the discovered relationship:
    X = exp(-decay*t) * (A*sin(w*t) + B*cos(w*t)) * (1 + C*I_light_prev) + D

    This represents a damped harmonic oscillator with light-dependent modulation.
    """
    # Parameters learned from the training data
    A = 1.370396326621365
    B = 1.470682804000514
    decay = 0.034232731739482
    w = 0.256176893849398
    C = 0.109112042847898
    D = 0.075260554494839

    results = []
    for row in input_data:
        t = row['t']
        I_light_prev = row['I_light_prev']

        # Compute the predicted X value
        oscillation = A * np.sin(w * t) + B * np.cos(w * t)
        damping = np.exp(-decay * t)
        light_modulation = 1 + C * I_light_prev

        X = damping * oscillation * light_modulation + D

        results.append({'X': float(X)})

    return results
