import math

# Generalized tight-binding (Morrison-type) law.
#
# The equilibrium bound complex C satisfies a quadratic equation
#
#       a(Lt) * C**2 + b(Lt) * C + c(Lt) = 0
#
# whose coefficients are cubic polynomials in the total ligand Lt.
# This is the algebraic relation obtained after eliminating the free
# ligand concentration from a saturable receptor-binding equilibrium
# (1:1 binding gives the classic Morrison quadratic with linear
# coefficients; the higher-order coefficients here capture the mild
# non-monotonic "hook" that makes C peak near Lt~11 and slowly decline).
#
# C is the physical (lower / minus) root:
#       C = ( -b - sqrt(b**2 - 4*a*c) ) / (2*a)
#
# Coefficients fitted on the training data (a0 fixed to 1 as the
# normalization of the C**2 term).

A = (1.0, 0.8276830130667815, 0.10368756377043116, 0.0018751969410872155)
B = (-0.7913095217652624, -2.463314450335477, -0.7940097696510907, -0.013985352171507228)
Cc = (-0.00013031381991832167, 0.7596403514474002, 1.2003700439173919, 0.012112116133895975)


def _poly(coef, x):
    return coef[0] + x * (coef[1] + x * (coef[2] + x * coef[3]))


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    Lt = float(row["Lt"])

    a = _poly(A, Lt)
    b = _poly(B, Lt)
    c = _poly(Cc, Lt)

    disc = b * b - 4.0 * a * c
    if disc < 0.0:
        disc = 0.0

    C = (-b - math.sqrt(disc)) / (2.0 * a)
    return [{"C": C}]
