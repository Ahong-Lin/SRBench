def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dN_dt from observed variables (t, N, reproductive_adult_abundance).

    Model: Polynomial regression including time-dependent terms
    This captures the dynamics of an experimental system where both the population (N)
    and reproductive adult abundance (rab) evolve over time according to coupled
    differential equations.
    """

    # Coefficients fitted to training data using polynomial regression
    # Model: dN_dt = sum of polynomial terms in (t, N, rab) up to degree 3
    coeffs = {
        'N': -115.1555526006,
        'rab': 112.9989819294,
        't': 2174.8571355830,
        'N^2': -0.3904739777,
        'rab^2': -5.1828498962,
        't^2': 183.8495070493,
        'N^3': 0.0061777655,
        'rab^3': 0.0190326688,
        't^3': -6.5874062040,
        'N*rab': 3.9697963102,
        'N*t': 16.2608312869,
        'rab*t': -47.7808066449,
        'N^2*rab': -0.0233047746,
        'N*rab^2': 0.0103528130,
        'const': 4066.5859554555,
    }

    results = []
    for row in input_data:
        t = row['t']
        N = row['N']
        rab = row['reproductive_adult_abundance']

        # Compute dN/dt using the fitted polynomial model
        dN_dt = (
            coeffs['const'] +
            coeffs['N'] * N +
            coeffs['rab'] * rab +
            coeffs['t'] * t +
            coeffs['N^2'] * (N ** 2) +
            coeffs['rab^2'] * (rab ** 2) +
            coeffs['t^2'] * (t ** 2) +
            coeffs['N^3'] * (N ** 3) +
            coeffs['rab^3'] * (rab ** 3) +
            coeffs['t^3'] * (t ** 3) +
            coeffs['N*rab'] * (N * rab) +
            coeffs['N*t'] * (N * t) +
            coeffs['rab*t'] * (rab * t) +
            coeffs['N^2*rab'] * (N * N * rab) +
            coeffs['N*rab^2'] * (N * rab * rab)
        )

        results.append({'dN_dt': dN_dt})

    return results
