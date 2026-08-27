def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dN_dt (rate of change of population N) from observed inputs.

    The model is a logistic growth equation with crowding inhibition:
    dN_dt = a*N - b*N² - c*N*crowding_load - d*crowding_load + e - f*N*crowding_load²

    Where:
    - a = 0.5698703173 (linear growth rate)
    - b = 0.000026077035 (intraspecific competition coefficient)
    - c = 0.000685901286 (N × crowding_load interaction)
    - d = 0.054120562421 (direct crowding effect)
    - e = -11.6203512943 (constant offset)
    - f = -0.00000017171124 (N × crowding_load² interaction)
    """

    # Model parameters
    a = 0.5698703173
    b = 0.000026077035
    c = 0.000685901286
    d = 0.054120562421
    e = -11.6203512943
    f = -0.00000017171124

    results = []

    for row in input_data:
        N = row['N']
        crowding_load = row['crowding_load']

        # Apply the model
        dN_dt = (a * N
                 - b * N**2
                 - c * N * crowding_load
                 - d * crowding_load
                 + e
                 - f * N * crowding_load**2)

        results.append({"dN_dt": dN_dt})

    return results
