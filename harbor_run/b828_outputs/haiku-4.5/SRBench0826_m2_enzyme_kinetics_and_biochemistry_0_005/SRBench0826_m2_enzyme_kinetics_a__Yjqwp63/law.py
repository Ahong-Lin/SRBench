def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict the instantaneous rate of change of active enzyme concentration (dE/dt)
    from the observed state variables E (active enzyme) and A (accumulated inactive forms).

    The law is a quadratic function of E and A:
    dE/dt = c0*E + c1*A + c2*E² + c3*A² + c4*E*A + intercept
    """

    # Fitted coefficients from training data
    c0 = -0.087538487862968
    c1 = 0.304735137417005
    c2 = -0.010591087961668
    c3 = 0.000005909759731
    c4 = 0.004511339382957
    intercept = -0.064472391012387

    results = []
    for row in input_data:
        E = row['E']
        A = row['A']

        # Compute dE/dt using the quadratic model
        dE_dt = c0*E + c1*A + c2*E**2 + c3*A**2 + c4*E*A + intercept

        results.append({'dE_dt': dE_dt})

    return results
