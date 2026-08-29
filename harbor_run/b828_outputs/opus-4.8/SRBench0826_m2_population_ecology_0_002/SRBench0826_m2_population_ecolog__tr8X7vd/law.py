"""Discovered law for prey dynamics dN/dt in a predator-prey reserve.

Model: Rosenzweig-MacArthur (logistic prey growth + Holling type II predation)

    dN/dt = r * N * (1 - N/K) - a * N * P / (1 + h * N)

Parameters were fit by nonlinear least squares on the training data:
    r = 0.79802985   (intrinsic prey growth rate)
    K = 99.9076146   (prey carrying capacity)
    a = 0.13054372   (attack / capture rate)
    h = 0.02194693   (handling time)

The auxiliary observed variable R and time t are not required: given (N, P)
the model explains the target with R^2 ~ 0.9998 (and ~0.9996 on a held-out
later time segment), so R carries no additional predictive information about
dN/dt beyond the mechanistic terms above.
"""

# Fixed constants inferred from the training data.
R_GROWTH = 0.79802985  # intrinsic prey growth rate r
K_CAP = 99.9076146     # carrying capacity K
A_ATTACK = 0.13054372  # attack rate a
H_HANDLE = 0.02194693  # handling time h


def law(input_data):
    """Map each input row independently to a dN_dt prediction.

    Args:
        input_data: list of dicts with keys 't', 'N', 'P', 'R'.

    Returns:
        list of dicts, each with a single key 'dN_dt'.
    """
    out = []
    for row in input_data:
        N = row["N"]
        P = row["P"]

        growth = R_GROWTH * N * (1.0 - N / K_CAP)
        predation = A_ATTACK * N * P / (1.0 + H_HANDLE * N)
        dN_dt = growth - predation

        out.append({"dN_dt": dN_dt})
    return out
