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

    # Coefficients from the fitted cubic model
    coef_dc = 0.181478101894
    coef_dc_squared = 0.035608558792
    coef_dc_cubed = 0.075914816916
    coef_dp_comp = 0.169103904312
    coef_dc_acc = 0.122357091092
    intercept = -0.003909440121

    for row in input_data:
        dc = row['dc']
        dp_comp = row['dp_comp']
        dc_acc = row['dc_acc']

        # Formula: dp = 0.18148*dc + 0.03561*dc^2 + 0.07591*dc^3 + 0.16910*dp_comp + 0.12236*dc_acc - 0.00391
        dp = (coef_dc * dc +
              coef_dc_squared * (dc ** 2) +
              coef_dc_cubed * (dc ** 3) +
              coef_dp_comp * dp_comp +
              coef_dc_acc * dc_acc +
              intercept)

        results.append({"dp": dp})

    return results
