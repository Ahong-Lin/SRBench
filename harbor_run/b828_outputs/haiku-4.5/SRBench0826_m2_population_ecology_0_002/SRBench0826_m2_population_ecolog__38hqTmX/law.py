def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dN_dt (rate of change of prey abundance) in a predator-prey system.

    Uses a polynomial regression model fitted to experimental data from a
    predator-prey system with stable abiotic conditions.

    The model captures the nonlinear coupled dynamics between prey (N) and
    predator (P) populations, with resource availability (R) and time (t)
    as additional factors.
    """
    # Model coefficients (from Ridge regression with alpha=0.001)
    c_intercept = -0.2227708089
    c_N = 1.1224588695
    c_P = 0.0964659522
    c_R = -19.7303822735
    c_NP = -0.0952737523
    c_NR = 0.2151153897
    c_PR = 1.1064786272
    c_N2 = -0.0112366651
    c_P2 = -0.0062855929
    c_R2 = -0.3473252406
    c_NPR = 0.0054392812

    results = []
    for row in input_data:
        N = row['N']
        P = row['P']
        R = row['R']

        # Polynomial model of the form:
        # dN/dt = c_intercept + c_N*N + c_P*P + c_R*R
        #         + c_NP*N*P + c_NR*N*R + c_PR*P*R
        #         + c_N2*N^2 + c_P2*P^2 + c_R2*R^2
        #         + c_NPR*N*P*R

        dN_dt = (c_intercept
                 + c_N * N
                 + c_P * P
                 + c_R * R
                 + c_NP * N * P
                 + c_NR * N * R
                 + c_PR * P * R
                 + c_N2 * N * N
                 + c_P2 * P * P
                 + c_R2 * R * R
                 + c_NPR * N * P * R)

        results.append({'dN_dt': dN_dt})

    return results
