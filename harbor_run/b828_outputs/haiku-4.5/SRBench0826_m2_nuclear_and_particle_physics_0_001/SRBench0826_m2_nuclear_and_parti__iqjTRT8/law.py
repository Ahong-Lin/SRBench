def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dNd_dt for a radioactive decay chain system.

    The daughter nuclide accumulation rate is modeled as a cubic polynomial
    function of the parent population (Np) and daughter population (Nd),
    with time-dependent coefficients.

    Formula:
    dNd_dt = c0*Np + c1*Np*t + c2*Np*t² + c3*Np*t³
           + c4*Nd + c5*Nd*t + c6*Nd*t² + c7*Nd*t³
           + c8

    Coefficients derived from training data using least-squares fitting.
    """
    # Fitted coefficients from degree-3 polynomial regression
    c = [
        7.33468121e-02,   # c0: Np
        2.60278444e-02,   # c1: Np*t
        -7.87440221e-04,  # c2: Np*t²
        2.42309811e-05,   # c3: Np*t³
        -4.90386728e-01,  # c4: Nd
        1.93097616e-02,   # c5: Nd*t
        -6.08482510e-04,  # c6: Nd*t²
        5.81015874e-06,   # c7: Nd*t³
        -4.74431277e+01   # c8: constant term
    ]

    results = []
    for row in input_data:
        t = row['t']
        Np = row['Np']
        Nd = row['Nd']

        # Compute polynomial terms
        dNd_dt = (
            c[0] * Np +
            c[1] * Np * t +
            c[2] * Np * t**2 +
            c[3] * Np * t**3 +
            c[4] * Nd +
            c[5] * Nd * t +
            c[6] * Nd * t**2 +
            c[7] * Nd * t**3 +
            c[8]
        )

        results.append({'dNd_dt': dNd_dt})

    return results
