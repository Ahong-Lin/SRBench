def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discover the rate of change of species N1 in a competitive two-species system.

    The discovered relationship is a quadratic polynomial model in N1, N2, and P1.

    Parameters:
    -----------
    input_data : list[dict[str, float]]
        Each dictionary contains:
        - t: time (not used in the model)
        - N1: abundance of species 1
        - N2: abundance of species 2
        - P1: parameter/factor 1

    Returns:
    --------
    list[dict[str, float]]
        List with single dictionary containing the predicted dN1_dt value
    """
    # Extract coefficients from training data fit
    # Model: dN1/dt = intercept + a_N1*N1 + a_N2*N2 + a_P1*P1
    #                  + a_N1_N1*N1^2 + a_N1_N2*N1*N2 + a_N1_P1*N1*P1
    #                  + a_N2_N2*N2^2 + a_N2_P1*N2*P1 + a_P1_P1*P1^2

    intercept = 0.0702528213
    a_N1 = 0.3891033511
    a_N2 = 0.0682697575
    a_P1 = -0.0882605181
    a_N1_N1 = -0.0040562405
    a_N1_N2 = -0.0019389231
    a_N1_P1 = -0.0179169770
    a_N2_N2 = -0.0005788953
    a_N2_P1 = -0.0001701445
    a_P1_P1 = 0.0039017378

    row = input_data[0]
    N1 = row['N1']
    N2 = row['N2']
    P1 = row['P1']

    dN1_dt = (
        intercept
        + a_N1 * N1
        + a_N2 * N2
        + a_P1 * P1
        + a_N1_N1 * (N1 * N1)
        + a_N1_N2 * (N1 * N2)
        + a_N1_P1 * (N1 * P1)
        + a_N2_N2 * (N2 * N2)
        + a_N2_P1 * (N2 * P1)
        + a_P1_P1 * (P1 * P1)
    )

    return [{"dN1_dt": dN1_dt}]
