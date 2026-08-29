import math

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the output variable based on the input variables according to a discovered law.

    The discovered law is a modulated oscillation model:
    X = a + b*sin(ω*t) + c*cos(ω*t) + d*I_light_prev*sin(ω*t) + e*I_light_prev*cos(ω*t)

    Args:
        input_data: A list of dictionaries, where each dictionary is a single data
                    point containing the input variable names ('t', 'I_light_prev')
                    as keys and their corresponding values.

    Returns:
        A list of dictionaries, corresponding to the input_data list, with each
        dictionary containing the predicted output variable, e.g. {"X": value}.
    """
    # Fitted parameters from optimization
    omega = 0.2627039516  # frequency parameter
    a = 0.0008376750      # constant offset
    b = 0.7668687405      # sine coefficient
    c = 0.0034794836      # cosine coefficient
    d = 0.5252106718      # I_light_prev * sine coefficient
    e = -0.0258803181     # I_light_prev * cosine coefficient

    results = []
    for row in input_data:
        t = row['t']
        I_light_prev = row['I_light_prev']

        # Compute the predicted X value
        sin_term = math.sin(omega * t)
        cos_term = math.cos(omega * t)

        X = a + b * sin_term + c * cos_term + d * I_light_prev * sin_term + e * I_light_prev * cos_term

        results.append({"X": X})

    return results
