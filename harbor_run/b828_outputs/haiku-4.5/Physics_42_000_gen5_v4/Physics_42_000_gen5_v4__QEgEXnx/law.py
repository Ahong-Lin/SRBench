import math

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the output variable based on the input variables according to a discovered law.

    Args:
        input_data: A list of dictionaries, where each dictionary is a single data
                    point containing the input variable name ('t') as a key and its
                    corresponding value.

    Returns:
        A list of dictionaries, corresponding to the input_data list, with each
        dictionary containing the predicted output variable, e.g. {"v": value}.
    """
    result = []

    # Fitted parameters from hyperbolic tangent model
    a = -15.8585782809
    b = 26.4331425965
    c = 0.3625923258
    d = 1.9185199092

    for row in input_data:
        t = row['t']
        v = a + b * math.tanh(c * (t + d))
        result.append({"v": v})

    return result
