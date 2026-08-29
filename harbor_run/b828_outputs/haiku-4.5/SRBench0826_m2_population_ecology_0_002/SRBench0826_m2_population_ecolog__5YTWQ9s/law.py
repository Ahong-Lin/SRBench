def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discovered law for predator-prey dynamics: dN/dt prediction.

    The relationship models the rate of change of prey population as a function
    of prey density (N), predator density (P), and a resource/environmental variable (R).

    The model is a quadratic multivariate function capturing:
    - Linear growth of prey (N term)
    - Predation pressure (N*P interaction)
    - Resource-dependent growth (N*R interaction)
    - Density-dependent effects (N², P², R² terms)
    - Complex environmental feedbacks (P*R interaction)
    """
    result = []

    # Coefficients from linear regression fit on polynomial features
    intercept = -0.1807232811
    coef_N = 1.2574134605
    coef_P = 0.1411002869
    coef_R = -29.7405972388
    coef_N2 = -0.0119413622
    coef_P2 = -0.0099315629
    coef_R2 = 0.2068215950
    coef_NR = 0.2765718939
    coef_NP = -0.0855256960
    coef_PR = 1.6421539679

    for row in input_data:
        N = row['N']
        P = row['P']
        R = row['R']

        # Compute dN/dt using the discovered polynomial model
        dN_dt = (
            intercept +
            coef_N * N +
            coef_P * P +
            coef_R * R +
            coef_N2 * (N * N) +
            coef_P2 * (P * P) +
            coef_R2 * (R * R) +
            coef_NR * (N * R) +
            coef_NP * (N * P) +
            coef_PR * (P * R)
        )

        result.append({'dN_dt': dN_dt})

    return result
