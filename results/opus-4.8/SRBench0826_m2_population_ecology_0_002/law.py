"""Discovered law for prey dynamics in a predator-prey reserve.

Model: Rosenzweig-MacArthur predator-prey.
    dN/dt = r * N * (1 - N/K)  -  a * N * P / (1 + b * N)

    - Logistic prey growth in the predator's absence (intrinsic rate r,
      carrying capacity K set by the enclosed reserve).
    - Holling type II predation: a saturating functional response with
      half-saturation controlled by b (handling / satiation).

The variable R (and t) carry no independent explanatory power once N and P
are known (see explain.md); they are not used.

Parameters fitted on /app/data/train_data.csv (R^2 = 0.99984, and R^2 = 0.9995
on a forward time-holdout that mimics the hidden test segment).
"""

# Fitted parameters
R_GROWTH = 0.7980298484715325   # r  : intrinsic prey growth rate
K_CAP    = 99.90761463361774    # K  : carrying capacity
A_ATTACK = 0.13054371923531993  # a  : attack rate
B_HANDLE = 0.021946927076735862 # b  : handling/saturation coefficient


def _dN_dt(N: float, P: float) -> float:
    growth = R_GROWTH * N * (1.0 - N / K_CAP)
    predation = A_ATTACK * N * P / (1.0 + B_HANDLE * N)
    return growth - predation


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Predict dN_dt for each observation.

    Args:
        input_data: list of dicts with keys 't', 'N', 'P', 'R'.

    Returns:
        list of dicts each with key 'dN_dt'.
    """
    out = []
    for row in input_data:
        N = float(row["N"])
        P = float(row["P"])
        out.append({"dN_dt": _dN_dt(N, P)})
    return out
