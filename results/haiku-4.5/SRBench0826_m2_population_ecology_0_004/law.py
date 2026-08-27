"""
Lotka-Volterra competition model with environmental parameter P1.

This model predicts dN1/dt (rate of change of species 1 abundance) from:
- N1: current abundance of species 1
- N2: current abundance of species 2 (competitor)
- P1: environmental/parameter variable

The model was fitted using polynomial regression (degree 2) on experimental
competition data, achieving R² ≈ 0.9999996 on the training set.
"""

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dN1_dt for competing plant species using fitted polynomial model.

    Args:
        input_data: List of dictionaries with keys 'N1', 'N2', 'P1'

    Returns:
        List of dictionaries with 'dN1_dt' predictions
    """
    # Fitted coefficients from polynomial regression
    intercept = 0.0702528213

    # Linear coefficients
    c_N1 = 0.3891033511
    c_N2 = 0.0682697575
    c_P1 = -0.0882605181

    # Quadratic coefficients
    c_N1_sq = -0.0040562405
    c_N1_N2 = -0.0019389231
    c_N1_P1 = -0.0179169770
    c_N2_sq = -0.0005788953
    c_N2_P1 = -0.0001701445
    c_P1_sq = 0.0039017378

    results = []
    for sample in input_data:
        N1 = sample['N1']
        N2 = sample['N2']
        P1 = sample['P1']

        # Polynomial prediction
        dN1_dt = (
            intercept
            + c_N1 * N1
            + c_N2 * N2
            + c_P1 * P1
            + c_N1_sq * N1**2
            + c_N1_N2 * N1 * N2
            + c_N1_P1 * N1 * P1
            + c_N2_sq * N2**2
            + c_N2_P1 * N2 * P1
            + c_P1_sq * P1**2
        )

        results.append({'dN1_dt': dN1_dt})

    return results
