"""Discovered law for the herd-immunity-threshold dataset.

Scientific target:  H_c  (critical immune fraction)
Input variable:     R0   (basic reproduction number / transmissibility)

Discovered closed form (interpretable, pointwise):

        a * ln(R0) + b
    H_c = ----------------------------
        R0 + c * sqrt(R0) + d

The numerator is linear in the log of transmissibility; the denominator is a
quadratic in sqrt(R0).  This single algebraic expression reproduces the
non-monotonic ("hump") behaviour of the data: H_c rises steeply just above the
epidemic threshold R0 = 1, peaks near R0 ~ 3.08, and then decays slowly.

Fitted constants (from /app/data/train_data.csv):
    a =  2.1193976787
    b =  0.5010329161
    c =  4.0388393954
    d = -1.1493858221

Accuracy on the training set: max |error| = 5.1e-5, max relative error = 1.9e-4.
The denominator stays strictly positive over the observed range R0 in [1.05, 8].
"""

import math

# Constants inferred from the training data (non-linear least squares).
A = 2.1193976787124220
B = 0.5010329160951027
C = 4.0388393953994170
D = -1.1493858221297364


def _predict(R0: float) -> float:
    q = math.sqrt(R0)
    numerator = A * math.log(R0) + B
    denominator = R0 + C * q + D
    return numerator / denominator


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    R0 = float(row["R0"])
    return [{"H_c": _predict(R0)}]
