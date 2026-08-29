def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts Brier score from logC using a quartic polynomial model.

    The discovered relationship is a degree-4 polynomial fitted to the training data:
    Brier = a*logC^4 + b*logC^3 + c*logC^2 + d*logC + e

    Coefficients fitted via curve_fit on the training dataset.
    """
    # Fitted coefficients from quartic regression
    a = -0.00058251
    b = 0.01080536
    c = 0.02320308
    d = -0.04122733
    e = 0.19560880

    results = []
    for row in input_data:
        logC = row["logC"]
        brier = a * logC**4 + b * logC**3 + c * logC**2 + d * logC + e
        results.append({"Brier": brier})

    return results
