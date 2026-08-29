def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dN1_dt based on the competitive Lotka-Volterra dynamics model.

    The discovered law is a polynomial model of the form:
    dN1/dt = b0 + b1*N1 + b2*N1² + b3*N1*N2 + b4*N2 + b5*N2² + b6*P1

    where the coefficients were obtained through least-squares fitting to the training data.
    """
    # Coefficients discovered through symbolic regression
    b0 = -73.982344959474
    b1 = -3.847962268779
    b2 = 0.023665432557
    b3 = 0.025818002877
    b4 = 3.609692454444
    b5 = -0.027666468464
    b6 = -0.615572895726

    result = []
    for row in input_data:
        N1 = row['N1']
        N2 = row['N2']
        P1 = row['P1']

        # Compute the polynomial model
        dN1_dt = (
            b0 +
            b1 * N1 +
            b2 * (N1 ** 2) +
            b3 * N1 * N2 +
            b4 * N2 +
            b5 * (N2 ** 2) +
            b6 * P1
        )

        result.append({'dN1_dt': dN1_dt})

    return result
