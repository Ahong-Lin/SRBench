def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dN_dt from N, A, S using the discovered linear law:
    dN_dt = 130.19086934 + 0.08002280*N - 3.19322512*A - 0.82764518*S

    This represents the rate of change of cell count in a confluency-limited culture.
    """
    # Coefficients from linear regression on training data (R² = 0.9838)
    intercept = 130.19086934
    coef_N = 0.08002280
    coef_A = -3.19322512
    coef_S = -0.82764518

    results = []
    for row in input_data:
        N = row['N']
        A = row['A']
        S = row['S']

        dN_dt = intercept + coef_N * N + coef_A * A + coef_S * S

        results.append({
            'dN_dt': dN_dt
        })

    return results
