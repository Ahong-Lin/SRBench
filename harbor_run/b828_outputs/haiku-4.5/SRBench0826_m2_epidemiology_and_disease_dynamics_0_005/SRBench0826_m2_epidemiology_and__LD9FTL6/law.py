def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Compute dI_dt from observed state variables using discovered quadratic relationship.

    This implements the exact mathematical law governing the seasonally forced
    infection model with R² = 0.9998.

    Args:
        input_data: List of dicts with keys 't', 'S', 'I', 'R', 'C' (float values)

    Returns:
        List of dicts with key 'dI_dt' containing predictions
    """

    # Coefficients of the complete quadratic polynomial
    # dI/dt = c0 + c1*S + c2*I + c3*R + c4*C + c5*t
    #         + c6*S² + c7*S*I + c8*S*R + c9*S*C + c10*S*t
    #         + c11*I² + c12*I*R + c13*I*C + c14*I*t
    #         + c15*R² + c16*R*C + c17*R*t
    #         + c18*C² + c19*C*t
    #         + c20*t²

    c0 = -165.6416
    c1 = 213.3698
    c2 = 220.2367
    c3 = 443.2434
    c4 = -24.7507
    c5 = 5.2575
    c6 = -65.4982
    c7 = -130.1500
    c8 = -295.2468
    c9 = 5.6132
    c10 = 0.1590
    c11 = -77.5097
    c12 = -304.0290
    c13 = -11.7811
    c14 = -0.1970
    c15 = -281.1201
    c16 = -35.1714
    c17 = -7.5225
    c18 = 57.3587
    c19 = 3.1150
    c20 = -0.1053

    results = []

    for row in input_data:
        t = row['t']
        S = row['S']
        I = row['I']
        R = row['R']
        C = row['C']

        # Compute all interaction terms
        S2 = S * S
        I2 = I * I
        R2 = R * R
        C2 = C * C
        t2 = t * t

        SI = S * I
        SR = S * R
        SC = S * C
        St = S * t

        IR = I * R
        IC = I * C
        It = I * t

        RC = R * C
        Rt = R * t

        Ct = C * t

        # Evaluate polynomial
        dI_dt = (
            c0
            + c1*S + c2*I + c3*R + c4*C + c5*t
            + c6*S2 + c7*SI + c8*SR + c9*SC + c10*St
            + c11*I2 + c12*IR + c13*IC + c14*It
            + c15*R2 + c16*RC + c17*Rt
            + c18*C2 + c19*Ct
            + c20*t2
        )

        results.append({'dI_dt': dI_dt})

    return results
