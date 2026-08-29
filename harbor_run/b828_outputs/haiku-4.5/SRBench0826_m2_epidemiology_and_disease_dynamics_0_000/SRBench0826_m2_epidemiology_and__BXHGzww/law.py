def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dI_dt for a SEIR-based epidemiological model with interaction terms.

    The discovered relationship is:
    dI_dt = 0.0266221353 + 2.5205055514*(S*I/N) + 0.0918997474*E
            - 2.3405946745*I + 0.0023089429*E*I + 0.0020921446*I*R

    where N = S + E + I + R (total population)
    """
    results = []

    for row in input_data:
        S = row["S"]
        E = row["E"]
        I = row["I"]
        R = row["R"]

        # Total population
        N = S + E + I + R

        # Coefficients (fitted from training data)
        const = 0.0266221353
        beta_coeff = 2.5205055514
        sigma_coeff = 0.0918997474
        gamma_coeff = -2.3405946745
        ei_coeff = 0.0023089429
        ir_coeff = 0.0020921446

        # Calculate dI_dt
        di_dt = (
            const
            + beta_coeff * (S * I / N)
            + sigma_coeff * E
            + gamma_coeff * I
            + ei_coeff * E * I
            + ir_coeff * I * R
        )

        results.append({"dI_dt": di_dt})

    return results
