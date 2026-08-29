def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Cubic polynomial model for predicting dN_dt from t, N, and reproductive_adult_abundance.

    Fitted on training data using degree-3 polynomial regression.
    R² = 0.8486, RMSE = 20.93
    """

    # Coefficients from the fitted cubic polynomial model
    coefficients = {
        '1': 219.8531701741757,
        't': -0.0032409068742346512,
        'N': -0.06953386814293447,
        'r_a_a': -0.006951984349453403,
        't^2': 0.029982215480744322,
        't*N': 0.5611225653165078,
        't*r_a_a': -0.17132817283309218,
        'N^2': 0.625956989078101,
        'N*r_a_a': -0.42586403185462557,
        'r_a_a^2': -0.6646354602916775,
        't^3': 0.3491522135078965,
        't^2*N': -2.98932163965709,
        't^2*r_a_a': 4.198132282676661,
        't*N^2': 0.05782872307952676,
        't*N*r_a_a': 0.13209127130487458,
        't*r_a_a^2': -0.30258548220633713,
        'N^3': 0.008506260201247126,
        'N^2*r_a_a': -0.044531271481554224,
        'N*r_a_a^2': 0.05889923694850426,
        'r_a_a^3': -0.018404840319764523
    }

    results = []
    for row in input_data:
        t = row['t']
        N = row['N']
        r_a_a = row['reproductive_adult_abundance']

        # Compute all polynomial terms up to degree 3
        dN_dt = (
            coefficients['1'] +
            coefficients['t'] * t +
            coefficients['N'] * N +
            coefficients['r_a_a'] * r_a_a +
            coefficients['t^2'] * (t**2) +
            coefficients['t*N'] * (t * N) +
            coefficients['t*r_a_a'] * (t * r_a_a) +
            coefficients['N^2'] * (N**2) +
            coefficients['N*r_a_a'] * (N * r_a_a) +
            coefficients['r_a_a^2'] * (r_a_a**2) +
            coefficients['t^3'] * (t**3) +
            coefficients['t^2*N'] * (t**2 * N) +
            coefficients['t^2*r_a_a'] * (t**2 * r_a_a) +
            coefficients['t*N^2'] * (t * N**2) +
            coefficients['t*N*r_a_a'] * (t * N * r_a_a) +
            coefficients['t*r_a_a^2'] * (t * r_a_a**2) +
            coefficients['N^3'] * (N**3) +
            coefficients['N^2*r_a_a'] * (N**2 * r_a_a) +
            coefficients['N*r_a_a^2'] * (N * r_a_a**2) +
            coefficients['r_a_a^3'] * (r_a_a**3)
        )

        results.append({'dN_dt': dN_dt})

    return results
