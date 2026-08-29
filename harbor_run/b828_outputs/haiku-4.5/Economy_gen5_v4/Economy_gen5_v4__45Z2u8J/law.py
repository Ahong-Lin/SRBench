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

    for row in input_data:
        dc = row['dc']
        pi = row['pi']
        dp_comp = row['dp_comp']
        sigma_c = row['sigma_c']
        dc_acc = row['dc_acc']

        # Degree 3 polynomial regression formula
        dp = (
            -0.01023695
            + 0.11531641 * dc
            + 0.02224453 * pi
            + 0.19882070 * dp_comp
            + 0.00860917 * sigma_c
            + 0.17425931 * dc_acc
            + 0.03103879 * dc**2
            + 0.19092339 * dc * pi
            + 0.00070563 * dc * dp_comp
            - 0.03608386 * dc * sigma_c
            - 0.00019561 * dc * dc_acc
            - 0.03495825 * pi**2
            - 0.02466629 * pi * dp_comp
            - 0.00749274 * pi * sigma_c
            - 0.00233092 * pi * dc_acc
            + 0.00669603 * dp_comp**2
            + 0.00133437 * dp_comp * sigma_c
            - 0.00360250 * dp_comp * dc_acc
            - 0.00810745 * sigma_c**2
            - 0.00635818 * sigma_c * dc_acc
            - 0.00053314 * dc_acc**2
            + 0.07614414 * dc**3
            + 0.01326794 * dc**2 * pi
            - 0.00041530 * dc**2 * dp_comp
            - 0.00422297 * dc**2 * sigma_c
            - 0.00021656 * dc**2 * dc_acc
            - 0.05304131 * dc * pi**2
            - 0.00203528 * dc * pi * dp_comp
            + 0.01643376 * dc * pi * sigma_c
            + 0.00050475 * dc * pi * dc_acc
            - 0.00030670 * dc * dp_comp**2
            + 0.00022895 * dc * dp_comp * sigma_c
            - 0.00018406 * dc * dp_comp * dc_acc
            + 0.00206329 * dc * sigma_c**2
            + 0.00071118 * dc * sigma_c * dc_acc
            + 0.00025223 * dc * dc_acc**2
            + 0.01735055 * pi**3
            + 0.01878114 * pi**2 * dp_comp
            + 0.00357248 * pi**2 * sigma_c
            - 0.00049635 * pi**2 * dc_acc
            - 0.00092170 * pi * dp_comp**2
            + 0.00439216 * pi * dp_comp * sigma_c
            + 0.00351334 * pi * dp_comp * dc_acc
            + 0.00658440 * pi * sigma_c**2
            + 0.00683420 * pi * sigma_c * dc_acc
            + 0.00088186 * pi * dc_acc**2
            - 0.04266121 * dp_comp**3
            - 0.01367409 * dp_comp**2 * sigma_c
            + 0.00183225 * dp_comp**2 * dc_acc
            + 0.00226103 * dp_comp * sigma_c**2
            + 0.00154924 * dp_comp * sigma_c * dc_acc
            + 0.00013985 * dp_comp * dc_acc**2
            + 0.00663320 * sigma_c**3
            + 0.00157408 * sigma_c**2 * dc_acc
            - 0.00010620 * sigma_c * dc_acc**2
            - 0.02061273 * dc_acc**3
        )

        results.append({"dp": dp})

    return results
