def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the output variable based on the input variables according to a discovered law.

    Args:
        input_data: A list of dictionaries, where each dictionary is a single data
                    point containing the input variable names
                    ('dc', 'pi', 'dp_comp', 'sigma_c', 'dc_acc') as keys and their
                    corresponding values.

    Returns:
        A list of dictionaries, corresponding to the input_data list, with each
        dictionary containing the predicted output variable, e.g. {"dp": value}.
    """
    results = []

    for data_point in input_data:
        dc = data_point['dc']
        pi = data_point['pi']
        dp_comp = data_point['dp_comp']
        sigma_c = data_point['sigma_c']
        dc_acc = data_point['dc_acc']

        # Polynomial regression formula (degree 2)
        dp = (
            0.021589 +  # intercept
            0.261433 * dc +
            0.004744 * pi +
            0.169611 * dp_comp +
            -0.011862 * sigma_c +
            0.127250 * dc_acc +
            -0.011221 * (dc ** 2) +
            0.141328 * (dc * pi) +
            0.001955 * (dc * dp_comp) +
            -0.025293 * (dc * sigma_c) +
            0.000817 * (dc * dc_acc) +
            0.004914 * (pi ** 2) +
            -0.007445 * (pi * dp_comp) +
            0.017655 * (pi * sigma_c) +
            -0.007579 * (pi * dc_acc) +
            0.003805 * (dp_comp ** 2) +
            0.008046 * (dp_comp * sigma_c) +
            -0.001615 * (dp_comp * dc_acc) +
            0.003209 * (sigma_c ** 2) +
            -0.000678 * (sigma_c * dc_acc) +
            -0.000250 * (dc_acc ** 2)
        )

        results.append({"dp": dp})

    return results
