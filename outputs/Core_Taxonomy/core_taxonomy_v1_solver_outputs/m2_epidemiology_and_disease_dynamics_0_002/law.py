"""Discovered law for R0 as a function of contact rate c and infectious period D.

The reproduction quantity R0 is well described by a smooth response surface that
is a polynomial of degree 5 in the log-transformed drivers u = ln(c), v = ln(D):

    ln R0 = sum_{i+j<=5} a_ij * u^i * v^j
    R0    = exp( ln R0 )

The leading terms are a_00 ~= -1, a_10 ~= 1, a_01 ~= 1, i.e. to first order
R0 ~= (1/e) * c * D, with the higher-order terms encoding the saturation /
turn-over of R0 at large contact rate and long infectious period (R0 peaks
near c ~ 6, D ~ 6 and declines afterwards). Coefficients were fit by ordinary
least squares on ln(R0) over the full training set.
"""

# (i, j) exponent pairs for u = ln(c), v = ln(D), and their fitted coefficients.
_TERMS = [
    (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
    (1, 0), (1, 1), (1, 2), (1, 3), (1, 4),
    (2, 0), (2, 1), (2, 2), (2, 3),
    (3, 0), (3, 1), (3, 2),
    (4, 0), (4, 1),
    (5, 0),
]
_COEF = [
    -1.00208538,  0.98037747, -0.06903474, -0.03229255, -0.00034389, 0.00074085,
     1.04650913, -0.36692073,  0.19634195, -0.05016461,  0.00412852,
    -0.26189938,  0.24776951, -0.09683704,  0.01076948,
     0.04764717, -0.06703584,  0.00926874,
    -0.01205372,  0.00474491,
    -0.00086139,
]

import math


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    c = float(row["c"])
    D = float(row["D"])

    u = math.log(c)
    v = math.log(D)

    ln_r0 = 0.0
    for (i, j), a in zip(_TERMS, _COEF):
        ln_r0 += a * (u ** i) * (v ** j)

    return [{"R0": math.exp(ln_r0)}]
