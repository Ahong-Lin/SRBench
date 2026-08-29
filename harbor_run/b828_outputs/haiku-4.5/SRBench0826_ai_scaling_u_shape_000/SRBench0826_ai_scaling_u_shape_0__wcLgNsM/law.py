def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict Brier score from logC using a polynomial + sinusoidal model.

    The model captures the non-monotonic relationship in the data using:
    - A 4th-order polynomial base
    - Two sinusoidal oscillation components with distinct frequencies
    """
    # Fitted parameters
    # Polynomial coefficients (4th order): p0*x^4 + p1*x^3 + p2*x^2 + p3*x + p4
    p0 = 0.00142634
    p1 = 0.01326148
    p2 = 0.01177603
    p3 = -0.05520702
    p4 = 0.20104978

    # First sinusoidal component: freq1 ≈ 0.39
    freq1 = 0.38965652
    A_sin1 = -0.04346462
    A_cos1 = -0.04107130

    # Second sinusoidal component: freq2 ≈ 0.63
    freq2 = 0.62648306
    A_sin2 = 0.02185428
    A_cos2 = -0.02006828

    results = []
    for row in input_data:
        logC = row['logC']

        # Evaluate polynomial
        poly_val = p0 * (logC ** 4) + p1 * (logC ** 3) + p2 * (logC ** 2) + p3 * logC + p4

        # Evaluate first sinusoidal component
        import math
        sin1_val = A_sin1 * math.sin(2 * math.pi * freq1 * logC) + A_cos1 * math.cos(2 * math.pi * freq1 * logC)

        # Evaluate second sinusoidal component
        sin2_val = A_sin2 * math.sin(2 * math.pi * freq2 * logC) + A_cos2 * math.cos(2 * math.pi * freq2 * logC)

        # Combine all components
        brier_pred = poly_val + sin1_val + sin2_val

        results.append({"Brier": brier_pred})

    return results
