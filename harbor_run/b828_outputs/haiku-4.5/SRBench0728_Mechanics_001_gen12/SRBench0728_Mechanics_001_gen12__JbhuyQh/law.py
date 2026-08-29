def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict instantaneous acceleration (dv_dt) from observed variables.

    Discovered formula through linear regression analysis:
    dv_dt = -1.0441*x - 0.0386*v - 0.1052*Fh - 0.0429*Fh2

    This linear relationship explains 99.977% of variance in the training data (R² = 0.99977).
    """
    results = []
    for row in input_data:
        dv_dt = (
            -1.0441 * row['x'] +
            -0.0386 * row['v'] +
            -0.1052 * row['Fh'] +
            -0.0429 * row['Fh2']
        )
        results.append({"dv_dt": dv_dt})

    return results
