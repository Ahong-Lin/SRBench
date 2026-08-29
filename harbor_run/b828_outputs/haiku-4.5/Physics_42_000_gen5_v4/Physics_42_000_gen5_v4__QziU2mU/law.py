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
    # Fitted cubic polynomial: v = a*t^3 + b*t^2 + c*t + d
    a = 0.1075364099
    b = -1.3244644224
    c = 6.0209230962
    d = 0.0724816970

    results = []
    for row in input_data:
        t = row['t']
        v = a * (t ** 3) + b * (t ** 2) + c * t + d
        results.append({'v': v})

    return results
