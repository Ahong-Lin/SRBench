def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    SEIR epidemiological model for predicting dI/dt (rate of change of infectious individuals).

    Discovered equation: dI/dt = β*S*I - α*E*I - γ*I + c
    where:
    - β = 0.00031616 (transmission rate)
    - α = 0.00091584 (E*I interaction coefficient)
    - γ = 0.14498967 (recovery rate)
    - c = 0.03011520 (baseline adjustment)

    This model explains 97.5% of variance (R² = 0.9749) in the training data.
    """
    beta = 0.00031616
    alpha = 0.00091584
    gamma = 0.14498967
    intercept = 0.03011520

    results = []
    for data_point in input_data:
        S = data_point['S']
        E = data_point['E']
        I = data_point['I']

        dI_dt = beta * S * I - alpha * E * I - gamma * I + intercept

        results.append({'dI_dt': dI_dt})

    return results
