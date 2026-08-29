def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dP_dt from quantum system state variables.

    Implements the discovered relationship:
    dP_dt = a₀ + a₁·C·(0.5 - P) + a₂·W + a₃·W² + a₄·W³

    where:
    - C: coupling strength
    - P: excited state population
    - W: phase or frequency parameter
    - a₀, a₁, a₂, a₃, a₄: fitted coefficients
    """
    # Fitted coefficients from training data
    a0 = 0.002419037422844
    a1 = 0.734529835901884
    a2 = -0.428061590801785
    a3 = 3.554085697449922
    a4 = -23.642304998862404

    result = []
    for row in input_data:
        C = row['C']
        P = row['P']
        W = row['W']

        # Compute dP_dt using discovered formula
        dP_dt = a0 + a1 * C * (0.5 - P) + a2 * W + a3 * W**2 + a4 * W**3

        result.append({'dP_dt': dP_dt})

    return result
