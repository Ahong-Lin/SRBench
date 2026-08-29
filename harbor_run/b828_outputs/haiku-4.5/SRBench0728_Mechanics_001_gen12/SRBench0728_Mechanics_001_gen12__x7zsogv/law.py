def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discovers the instantaneous acceleration law from experimental data.

    The underlying relationship is:
    dv_dt = -1.043911*x - 0.039614*v - 0.104887*Fh - 0.046067*Fh2 - 0.000352

    This represents a damped oscillator system with external forcing.
    """
    results = []

    # Fitted coefficients from linear regression
    coef_x = -1.043911
    coef_v = -0.039614
    coef_Fh = -0.104887
    coef_Fh2 = -0.046067
    intercept = -0.000352

    for row in input_data:
        x = row['x']
        v = row['v']
        Fh = row['Fh']
        Fh2 = row['Fh2']

        dv_dt = coef_x * x + coef_v * v + coef_Fh * Fh + coef_Fh2 * Fh2 + intercept
        results.append({'dv_dt': dv_dt})

    return results
