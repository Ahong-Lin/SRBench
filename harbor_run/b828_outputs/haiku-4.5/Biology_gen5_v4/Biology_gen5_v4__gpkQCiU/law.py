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
    import numpy as np

    result = []
    for row in input_data:
        t = row['t']
        I_light_prev = row['I_light_prev']

        # Discovered law with interaction term
        # X = 0.7669 * sin(0.2625 * t) + 0.0017 * I_light_prev + 0.5247 * sin(0.2625 * t) * I_light_prev
        sin_t = np.sin(0.26253555 * t)
        x_pred = (0.76688731 * sin_t +
                  0.00170049 * I_light_prev +
                  0.52468886 * sin_t * I_light_prev -
                  0.00063492)

        result.append({"X": x_pred})

    return result
