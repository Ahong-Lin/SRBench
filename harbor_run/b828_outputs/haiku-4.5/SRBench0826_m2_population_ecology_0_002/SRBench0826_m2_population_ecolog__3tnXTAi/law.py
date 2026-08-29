def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Reconstructs dN_dt (prey population growth rate) from predator-prey dynamics.

    Uses a degree-2 polynomial regression model fitted to the training data.
    The model captures the nonlinear interactions between prey (N), predator (P),
    and environmental factor (R), as well as temporal (t) effects.
    """
    # Coefficients from polynomial regression (degree 2)
    # dN_dt = c0 + c1*N + c2*P + c3*R + c4*t + c5*N² + c6*NP + c7*NR
    #         + c8*Nt + c9*P² + c10*PR + c11*Pt + c12*R² + c13*Rt + c14*t²

    c0 = -0.329761923388543
    c1 = 1.310168829653825      # N
    c2 = 0.166963048277348      # P
    c3 = -31.682662177639845    # R
    c4 = 0.001688194365218      # t
    c5 = -0.011369337764255     # N²
    c6 = -0.091503423321605     # N*P
    c7 = 0.248586059180907      # N*R
    c8 = -0.000432099008862     # N*t
    c9 = -0.007316029448080     # P²
    c10 = 1.669931388341367     # P*R
    c11 = -0.000494578539582    # P*t
    c12 = 0.993029668477394     # R²
    c13 = -0.001099786116210    # R*t
    c14 = -0.000000003923346    # t²

    results = []
    for row in input_data:
        N = row['N']
        P = row['P']
        R = row['R']
        t = row['t']

        # Compute dN_dt using the polynomial model
        dN_dt = (
            c0
            + c1 * N
            + c2 * P
            + c3 * R
            + c4 * t
            + c5 * N * N
            + c6 * N * P
            + c7 * N * R
            + c8 * N * t
            + c9 * P * P
            + c10 * P * R
            + c11 * P * t
            + c12 * R * R
            + c13 * R * t
            + c14 * t * t
        )

        results.append({'dN_dt': dN_dt})

    return results
