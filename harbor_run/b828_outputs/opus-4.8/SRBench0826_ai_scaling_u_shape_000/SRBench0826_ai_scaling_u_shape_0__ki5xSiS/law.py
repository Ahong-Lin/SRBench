"""Discovered scaling law for Brier score vs. log-compute.

Model:  Brier(logC) = a*logC^2 + b*logC + c
                       + A1*exp(-(logC-m1)^2 / (2*s1^2))   # primary bump near logC=-1
                       + A2*exp(-(logC-m2)^2 / (2*s2^2))   # broad right-side correction
                       + A3*exp(-(logC-m3)^2 / (2*s3^2))   # narrow right-side correction

Parameters were fit with non-linear least squares on /app/data/train_data.csv.
Fit quality: RMSE = 4.8e-4, max abs error = 1.9e-3 over the full logC range.
"""

import math

# Quadratic trend
A_QUAD = 0.021269307349341574
B_LIN = 0.07313878455505843
C_CONST = 0.30001053900439967

# Gaussian components: (amplitude, center, sigma)
GAUSSIANS = (
    (0.19475481077207343, -0.9991367455894591, 0.34775168413876273),
    (-0.2574484372375788, 1.9010168192587336, 1.8585191840181898),
    (0.04307129568971827, 1.8497248045721983, 0.40719157786033244),
)


def _brier(logC: float) -> float:
    val = A_QUAD * logC * logC + B_LIN * logC + C_CONST
    for amp, mu, sigma in GAUSSIANS:
        val += amp * math.exp(-((logC - mu) ** 2) / (2.0 * sigma * sigma))
    return val


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Return one {"Brier": value} prediction for every input row."""
    return [{"Brier": _brier(float(row["logC"]))} for row in input_data]
