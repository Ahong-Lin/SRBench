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
    # Discovered polynomial model: degree 6
    # Coefficients from fitting training data
    c = [
        7.866280399665904e-02,
        5.861370061287314e+00,
        -8.951128011734820e-01,
        -2.783193268047896e-01,
        1.502691043087575e-01,
        -2.622251649925361e-02,
        1.673927260066365e-03
    ]

    results = []
    for item in input_data:
        t = item['t']
        # v = c0 + c1*t + c2*t^2 + c3*t^3 + c4*t^4 + c5*t^5 + c6*t^6
        v = c[0] + c[1]*t + c[2]*t**2 + c[3]*t**3 + c[4]*t**4 + c[5]*t**5 + c[6]*t**6
        results.append({'v': v})

    return results
