"""Discovered scaling law: Brier as a function of logC.

Brier(logC) = P(logC) + sum_k A_k * exp(-(logC - mu_k)^2 / (2 * sigma_k^2))

where P is a smooth degree-8 polynomial "baseline" scaling trend and each
Gaussian term is a localized bump/emergent feature. Parameters were fit by
non-linear least squares (scipy.curve_fit) on /app/data/train_data.csv.
"""

import math

# Degree-8 polynomial baseline coefficients (highest power first),
# evaluated Horner-style, i.e. c[0]*x^8 + ... + c[8].
_POLY = [
    2.233142918162149e-06,
    -5.9066420124800244e-06,
    -9.799232983203668e-05,
    6.078134873128296e-05,
    0.0015998109581476796,
    0.004933106187847568,
    0.017588231439906243,
    -0.006452084556764116,
    0.1467719141682848,
]

# Localized Gaussian terms: (amplitude A, center mu, width sigma)
_GAUSS = [
    (0.19909899167149223, -1.000278939144127, 0.35297576803391606),
    (0.045629946142286305, 1.7781395012138632, 0.37606097509589576),
    (0.016708767421058642, 2.329199070615217, 0.3483953566342187),
]


def _brier(logC: float) -> float:
    # Polynomial baseline (Horner).
    val = 0.0
    for c in _POLY:
        val = val * logC + c
    # Localized Gaussian contributions.
    for A, mu, sigma in _GAUSS:
        val += A * math.exp(-((logC - mu) ** 2) / (2.0 * sigma * sigma))
    return val


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Return one {"Brier": value} prediction for every input row."""
    out = []
    for row in input_data:
        out.append({"Brier": _brier(float(row["logC"]))})
    return out
