def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Extended SEIR epidemiological model for predicting dI/dt.

    The discovered relationship is:
    dI/dt = β*(S*I) + σ*E - γ*I - α*I² + const

    Where:
    - β = 0.00043113 (transmission rate coefficient)
    - σ = 0.10579054 (rate of progression from E to I)
    - γ = -0.26229735 (net recovery rate)
    - α = -0.00190901 (quadratic damping coefficient)
    - const = 0.0434542533 (constant offset)
    """
    # Constants from fitting
    beta = 0.00043113
    sigma = 0.10579054
    gamma = -0.26229735
    alpha = -0.00190901
    const = 0.0434542533

    results = []
    for row in input_data:
        S = row['S']
        E = row['E']
        I = row['I']

        # Compute dI/dt using the discovered equation
        # dI/dt = β*(S*I) + σ*E - γ*I - α*I²
        dI_dt = (beta * S * I +
                 sigma * E +
                 gamma * I +
                 alpha * I * I +
                 const)

        results.append({'dI_dt': dI_dt})

    return results
