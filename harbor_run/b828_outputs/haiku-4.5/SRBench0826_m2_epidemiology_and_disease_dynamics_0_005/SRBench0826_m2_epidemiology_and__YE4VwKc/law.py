def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discovered law for dI/dt in seasonally forced infection dynamics.

    Model: dI/dt = (β₀ + β₁*cos(ω*t)) * S * I - γ*I - α*I² - β_C*C - β_C2*C²

    Where:
    - β(t) = β₀ + β₁*cos(ω*t) is the seasonally modulated transmission rate
    - S, I are susceptible and infected populations
    - γ is the net recovery/removal rate (accounting for vital rates)
    - α is the quadratic self-limiting term in I (density dependence)
    - β_C, β_C2 parameterize the cumulative infection effect

    Physical interpretation:
    - The periodically forced transmission captures annual environmental cycles
    - Quadratic I² term represents crowding effects and nonlinear disease dynamics
    - Cumulative C effects suggest disease-induced behavioral changes or immunity structure
    """
    # Fitted parameters (optimized on training data)
    b0 = 3.98441727
    b1 = 0.89631399
    omega = 6.29182270  # Period ≈ 0.999 years (annual cycle)
    gamma = 0.03638749
    alpha_I2 = 26.08512613
    beta_C = -0.14609756
    beta_C2 = -0.44110365

    import math

    results = []
    for row in input_data:
        t = row['t']
        S = row['S']
        I = row['I']
        C = row['C']

        # Compute transmission rate with seasonal forcing
        beta_t = b0 + b1 * math.cos(omega * t)

        # Compute dI/dt
        dI_dt = beta_t * S * I - gamma * I - alpha_I2 * I * I + beta_C * C + beta_C2 * C * C

        results.append({'dI_dt': dI_dt})

    return results
