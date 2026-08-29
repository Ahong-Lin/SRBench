"""
Discovered law for quantum tunneling oscillation: dPr_dt prediction.

The relationship is a linear combination of the input variables:
dPr_dt = const + a*t + b*Pr + c*J + d*K + e*N
"""


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dPr_dt (rate of probability change) from input variables.

    Args:
        input_data: List containing exactly one dict with keys: t, Pr, J, K, N

    Returns:
        List containing one dict with key dPr_dt and the predicted value
    """
    # Coefficients obtained from multivariate linear regression on training data
    CONST = -0.0886491799
    COEF_T = 0.0004403681
    COEF_PR = -0.0471861930
    COEF_J = -0.2978532873
    COEF_K = 0.8077587228
    COEF_N = 0.1703447076

    row = input_data[0]
    t = row['t']
    Pr = row['Pr']
    J = row['J']
    K = row['K']
    N = row['N']

    dPr_dt = (
        CONST
        + COEF_T * t
        + COEF_PR * Pr
        + COEF_J * J
        + COEF_K * K
        + COEF_N * N
    )

    return [{'dPr_dt': dPr_dt}]
