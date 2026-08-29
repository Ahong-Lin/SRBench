def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dN_dt (instantaneous growth rate) from cell culture parameters.

    Model: dN_dt = c0 + c1*N + c2*S + c3*A + c4*N*A + c5*S*A + c6*t

    Where:
    - t: time
    - N: cell count
    - S: some measure related to space/structure
    - A: available space factor (contact inhibition parameter)
    - dN_dt: growth rate (cells per unit time)
    """
    # Fitted coefficients from training data (R² = 0.9996)
    c0 = -83.57392997908212
    c1 = 0.08481767484003142
    c2 = -0.870020632402006
    c3 = -1.885614097976483
    c4 = 0.004474504098823629
    c5 = -0.033922153290928604
    c6 = 0.31292052518462726

    results = []
    for row in input_data:
        t = row['t']
        N = row['N']
        S = row['S']
        A = row['A']

        dN_dt = (c0 +
                 c1 * N +
                 c2 * S +
                 c3 * A +
                 c4 * N * A +
                 c5 * S * A +
                 c6 * t)

        results.append({'dN_dt': dN_dt})

    return results
