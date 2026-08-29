def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discovers and predicts the instantaneous rate of change dN_dt
    for an observed dynamical system based on fitted coefficients.

    Fitted formula:
    dN_dt = a0 + a1*N + a2*rab + a3*t + a4*N*rab + a5*N*t + a6*rab*t
            + a7*N^2*t + a8*rab^3 + a9*N^3*t + a10*N^2 + a11*N^3

    where:
    - t: time variable
    - N: population abundance
    - rab: reproductive_adult_abundance (carrying capacity-like parameter)
    """

    # Fitted coefficients from regression analysis
    coefficients = {
        'const': 3395.915725627308,
        'N': 16.867814881805,
        'rab': -56.554117263516,
        't': -5040.940335629395,
        'N*rab': -0.142574828154,
        'N*t': 84.541733220586,
        'rab*t': -13.594808981669,
        'N^2*t': -0.353173716902,
        'rab^3': 0.002107219454,
        'N^3*t': 0.000536169791,
        'N^2': 0.037502771807,
        'N^3': -0.000346658301,
    }

    results = []

    for row in input_data:
        t_val = row['t']
        N_val = row['N']
        rab_val = row['reproductive_adult_abundance']

        # Compute basis functions
        N2 = N_val ** 2
        N3 = N_val ** 3
        rab3 = rab_val ** 3

        # Linear combination with fitted coefficients
        dN_dt_pred = (
            coefficients['const'] +
            coefficients['N'] * N_val +
            coefficients['rab'] * rab_val +
            coefficients['t'] * t_val +
            coefficients['N*rab'] * (N_val * rab_val) +
            coefficients['N*t'] * (N_val * t_val) +
            coefficients['rab*t'] * (rab_val * t_val) +
            coefficients['N^2*t'] * (N2 * t_val) +
            coefficients['rab^3'] * rab3 +
            coefficients['N^3*t'] * (N3 * t_val) +
            coefficients['N^2'] * N2 +
            coefficients['N^3'] * N3
        )

        results.append({'dN_dt': dN_dt_pred})

    return results
