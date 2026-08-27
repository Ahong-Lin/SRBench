"""Discovered law for coherent tunneling oscillation between two wells.

    dPr_dt = K * N - 0.1 * Pr + 0.05

Discovered via polynomial symbolic regression over {Pr, J, K, N}; this
expression reproduces the training data to machine precision
(max abs error ~2e-16).
"""

# Fitted constants (recovered exactly from the training data).
ALPHA = 1.0    # coefficient of the K*N tunneling-current term
BETA = 0.1     # linear relaxation/drift coefficient on Pr
GAMMA = 0.05   # constant drive/offset


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Predict dPr_dt for each observation.

    Parameters
    ----------
    input_data : list of dict
        Each dict has keys 't', 'Pr', 'J', 'K', 'N'.

    Returns
    -------
    list of dict
        Each dict has key 'dPr_dt' with the predicted value.
    """
    out = []
    for row in input_data:
        Pr = row["Pr"]
        K = row["K"]
        N = row["N"]
        dPr_dt = ALPHA * K * N - BETA * Pr + GAMMA
        out.append({"dPr_dt": dPr_dt})
    return out
