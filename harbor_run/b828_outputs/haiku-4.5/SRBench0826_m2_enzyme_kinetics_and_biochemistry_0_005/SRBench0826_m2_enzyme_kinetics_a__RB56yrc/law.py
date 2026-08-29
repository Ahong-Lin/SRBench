def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dE_dt from enzyme kinetics variables using a cubic polynomial model.

    The model is fitted from experimental enzyme denaturation data where:
    - E: concentration of active enzyme
    - A: concentration of inactive (denatured) enzyme
    - G: concentration of aggregated enzyme
    - t: time (included in input but not used in this model)

    The discovered law is a cubic polynomial in A and G:
    dE_dt = c0 + c1*A + c2*G + c3*A^2 + c4*A*G + c5*G^2 + c6*A^3 + c7*A^2*G + c8*A*G^2 + c9*G^3
    """
    result = []

    # Model coefficients (fitted from training data)
    c0 = -1.9826881835
    c1 = 0.5080957611
    c2 = 0.0043644965
    c3 = 0.0064959587
    c4 = 0.0133988062
    c5 = 0.0113178944
    c6 = -0.0039993367
    c7 = -0.0046492263
    c8 = -0.0025341038
    c9 = -0.0003201580

    for row in input_data:
        A = row['A']
        G = row['G']

        # Compute the cubic polynomial
        dE_dt = (c0 +
                 c1 * A +
                 c2 * G +
                 c3 * A * A +
                 c4 * A * G +
                 c5 * G * G +
                 c6 * A * A * A +
                 c7 * A * A * G +
                 c8 * A * G * G +
                 c9 * G * G * G)

        result.append({'dE_dt': dE_dt})

    return result
