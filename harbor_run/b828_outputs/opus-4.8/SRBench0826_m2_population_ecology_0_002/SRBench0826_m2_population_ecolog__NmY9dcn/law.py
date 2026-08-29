"""Discovered law for prey dynamics dN/dt in a predator-prey reserve.

Model: Rosenzweig-MacArthur (logistic prey growth + Holling type-II predation)

    dN/dt = r * N * (1 - N/K) - a * N * P / (1 + a * h * N)

Fitted on /app/data/train_data.csv (R^2 = 0.99984; robust to a train/test
time split). The prey right-hand side depends only on N (prey) and P
(predator); the auxiliary resource variable R does not enter the prey
equation (verified: adding any R term yields negligible improvement).
"""

# Parameters inferred from the training data (nonlinear least squares).
R_GROWTH = 0.798029847511997   # intrinsic prey growth rate r
K_CAP    = 99.90761458451203   # prey carrying capacity K
A_ATTACK = 0.1305437209264428  # predator attack rate a
H_HANDLE = 0.1681193669973549  # handling time h (max intake per predator = 1/h)


def _dN_dt(N: float, P: float) -> float:
    growth = R_GROWTH * N * (1.0 - N / K_CAP)
    predation = A_ATTACK * N * P / (1.0 + A_ATTACK * H_HANDLE * N)
    return growth - predation


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to one dN_dt prediction."""
    out = []
    for row in input_data:
        N = float(row["N"])
        P = float(row["P"])
        out.append({"dN_dt": _dN_dt(N, P)})
    return out
