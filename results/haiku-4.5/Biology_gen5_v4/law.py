import numpy as np

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the output variable based on the input variables according to a discovered law.

    Args:
        input_data: A list of dictionaries, where each dictionary is a single data
                    point containing the input variable names ('t', 'I_light_prev')
                    as keys and their corresponding values.

    Returns:
        A list of dictionaries, corresponding to the input_data list, with each
        dictionary containing the predicted output variable, e.g. {"X": value}.
    """
    # Extracted parameters from optimization
    a = -0.1142655094
    b = -0.0103269689
    c = -0.8074794943
    d = -0.3089308948
    e = 0.5272462309
    f = 0.0497074238
    g = 1.2066931340
    h = 0.2661650893
    i = 0.0096782720
    k = -0.4056231978
    l = -0.2444543453
    m = -1.0744080074
    n = -0.0943949542

    results = []
    for data_point in input_data:
        t = data_point['t']
        I_light_prev = data_point['I_light_prev']

        # Formula: X = a*sin(b*t + c*I_light) + d*cos(e*t + f*I_light) + g*sin(h*t + i*I_light) + k*cos(l*t + m*I_light) + n
        X = (a * np.sin(b * t + c * I_light_prev) +
             d * np.cos(e * t + f * I_light_prev) +
             g * np.sin(h * t + i * I_light_prev) +
             k * np.cos(l * t + m * I_light_prev) + n)

        results.append({"X": float(X)})

    return results
