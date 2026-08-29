def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discovered mathematical law for quantum system population transfer rate (dP_dt).

    The hidden law is a linear regression model:
    dP_dt = 0.000262937*t - 0.488270*P + 0.427808*C + 0.010309*W + 0.008676*N - 0.003763

    This relationship accurately describes the coherent population dynamics in a two-level
    quantum system driven by resonant coupling, with R² = 0.9988551.
    """
    result = []

    # Coefficients from linear regression
    coeff_t = 0.00026293689886003444
    coeff_P = -0.48826981254828594
    coeff_C = 0.42780819027417416
    coeff_W = 0.010309346369941285
    coeff_N = 0.008676408034660747
    intercept = -0.0037630024924815396

    for row in input_data:
        t = row['t']
        P = row['P']
        C = row['C']
        W = row['W']
        N = row['N']

        # Linear combination
        dP_dt = (
            coeff_t * t +
            coeff_P * P +
            coeff_C * C +
            coeff_W * W +
            coeff_N * N +
            intercept
        )

        result.append({'dP_dt': dP_dt})

    return result
