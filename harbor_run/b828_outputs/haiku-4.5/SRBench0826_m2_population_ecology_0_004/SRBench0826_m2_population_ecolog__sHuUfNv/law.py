def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dN1_dt from the competitive dynamics model.

    The discovered law is a quadratic function in the input variables:
    dN1_dt = c0 + c1*N1 + c2*N2 + c3*P1 + c4*N1^2 + c5*N2^2 + c6*P1^2 + c7*N1*N2 + c8*N1*P1 + c9*N2*P1

    These coefficients were fitted from the training data with R^2 = 0.99999963.
    """
    # Fitted coefficients from least-squares regression
    coeffs = {
        'c0': 0.070252821,
        'c1': 0.389103351,    # N1
        'c2': 0.068269757,    # N2
        'c3': -0.088260518,   # P1
        'c4': -0.004056240,   # N1^2
        'c5': -0.000578895,   # N2^2
        'c6': 0.003901738,    # P1^2
        'c7': -0.001938923,   # N1*N2
        'c8': -0.017916977,   # N1*P1
        'c9': -0.000170144,   # N2*P1
    }

    results = []
    for row in input_data:
        N1 = row['N1']
        N2 = row['N2']
        P1 = row['P1']

        dN1_dt = (
            coeffs['c0'] +
            coeffs['c1'] * N1 +
            coeffs['c2'] * N2 +
            coeffs['c3'] * P1 +
            coeffs['c4'] * N1 * N1 +
            coeffs['c5'] * N2 * N2 +
            coeffs['c6'] * P1 * P1 +
            coeffs['c7'] * N1 * N2 +
            coeffs['c8'] * N1 * P1 +
            coeffs['c9'] * N2 * P1
        )

        results.append({'dN1_dt': dN1_dt})

    return results
