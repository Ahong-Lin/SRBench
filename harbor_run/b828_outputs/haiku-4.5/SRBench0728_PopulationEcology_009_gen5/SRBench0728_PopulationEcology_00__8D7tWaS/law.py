def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dN_dt using a cubic polynomial model fitted to population dynamics data.

    The model was derived through symbolic regression analysis of the training dataset,
    which exhibits characteristics of population dynamics with environmental crowding effects.
    """

    # Fitted coefficients from training data (R² = 0.9899)
    c = [
        -23.3713903971,      # constant
        0.6550622620,        # N
        -0.1334344484,       # crowding_load
        -0.0009244579,       # N * crowding_load
        0.0000285841,        # N²
        0.0002266124,        # crowding_load²
        -0.0000002352,       # N³
        0.0000002453,        # crowding_load³
        0.0000008155,        # N² * crowding_load
        -0.0000006937,       # N * crowding_load²
    ]

    results = []
    for row in input_data:
        N = row['N']
        C = row['crowding_load']

        # Compute the polynomial
        dN_dt = (
            c[0] +
            c[1] * N +
            c[2] * C +
            c[3] * N * C +
            c[4] * N**2 +
            c[5] * C**2 +
            c[6] * N**3 +
            c[7] * C**3 +
            c[8] * N**2 * C +
            c[9] * N * C**2
        )

        results.append({"dN_dt": dN_dt})

    return results
