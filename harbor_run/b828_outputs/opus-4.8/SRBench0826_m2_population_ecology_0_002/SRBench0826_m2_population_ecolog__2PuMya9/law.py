"""Discovered law for the predator-prey reserve experiment.

The instantaneous prey growth rate dN/dt follows the Rosenzweig-MacArthur
model: logistic prey growth limited by carrying capacity, minus predation
described by a Holling type II (saturating) functional response.

    dN/dt = r * N * (1 - N / K) - a * N * P / (1 + b * N)

Parameters were fitted on /app/data/train_data.csv (R^2 = 0.99984, and
R^2 = 0.999 on a held-out right-hand time segment). The auxiliary column R
was found to be redundant for predicting dN/dt (adding it does not improve
the fit), so the law depends only on N and P.
"""

# Fitted constants (Rosenzweig-MacArthur)
R_GROWTH = 0.7980298484715325   # intrinsic prey growth rate r
K_CAP    = 99.90761463361774    # prey carrying capacity K
A_ATTACK = 0.13054371923531993  # predator attack rate a
B_HANDLE = 0.021946927076735862 # handling/saturation coefficient b


def law(input_data):
    """Map each input row independently to a dN_dt prediction.

    Args:
        input_data: list of dicts with keys 't', 'N', 'P', 'R'.

    Returns:
        list with exactly one dict {'dN_dt': value} per input row.
    """
    out = []
    for row in input_data:
        N = row["N"]
        P = row["P"]
        growth = R_GROWTH * N * (1.0 - N / K_CAP)
        predation = A_ATTACK * N * P / (1.0 + B_HANDLE * N)
        out.append({"dN_dt": growth - predation})
    return out
