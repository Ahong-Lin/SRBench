def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dN_dt using polynomial regression model with interaction terms.

    Model: dN_dt = c0 + c1*N + c2*t + c3*K + c4*N² + c5*t² + c6*K² + c7*N*t + c8*N*K + c9*t*K
    where K is crowding_load
    """
    # Fitted coefficients from training data
    c0 = -60.2947421745
    c1 = 0.7440546392
    c2 = -18.1884880244
    c3 = 0.3107118590
    c4 = -0.0003967880
    c5 = 0.1049013673
    c6 = -0.0006595699
    c7 = -0.0032171544
    c8 = 0.0001769297
    c9 = 0.0137086915

    results = []
    for row in input_data:
        N = row['N']
        t = row['t']
        K = row['crowding_load']

        # Calculate prediction
        dN_dt = (c0 +
                 c1 * N +
                 c2 * t +
                 c3 * K +
                 c4 * N**2 +
                 c5 * t**2 +
                 c6 * K**2 +
                 c7 * N * t +
                 c8 * N * K +
                 c9 * t * K)

        results.append({'dN_dt': dN_dt})

    return results
