def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dP_dt from quantum system state variables using a linear model.

    The governing equation is:
    dP/dt = -0.0029049 + 0.4322*C + 0.0085415*N + 0.077445*W - 0.5267*P

    Args:
        input_data: List of dictionaries with keys 't', 'P', 'C', 'W', 'N'

    Returns:
        List of dictionaries with keys 't', 'P', 'C', 'W', 'N', 'dP_dt_predicted'
    """
    # Coefficients from least-squares fit to training data
    a0 = -0.002904887297109
    a1 = 0.432176899738639   # C coefficient
    a2 = 0.008541492244687   # N coefficient
    a3 = 0.077445390249074   # W coefficient
    a4 = -0.526731965284364  # P coefficient

    result = []
    for point in input_data:
        C = point['C']
        N = point['N']
        W = point['W']
        P = point['P']

        dP_dt = a0 + a1 * C + a2 * N + a3 * W + a4 * P

        result.append({
            't': point['t'],
            'P': point['P'],
            'C': point['C'],
            'W': point['W'],
            'N': point['N'],
            'dP_dt_predicted': dP_dt
        })

    return result
