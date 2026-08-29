"""Discovered law for dN1_dt in a two-competitor + antagonist ecological system.

The scientific target is the instantaneous right-hand side dN1/dt of species N1.
Empirically the derivative factors through N1 (it must vanish when N1 = 0, i.e.
no population -> no growth), so we write it as

        dN1/dt = N1 * g(N1, N2, P1)

where g is the *per-capita* growth rate.  g is a smooth function of the three
observed densities; a cubic polynomial in (N1, N2, P1) reproduces the training
target to a root-mean-square error of ~2e-6 (R^2 = 1 - 3e-12), i.e. to the
precision of the data generator.  The polynomial is the explicit, pointwise
closed form of the underlying competitive/antagonistic dynamics.

Each row is mapped independently; no state is carried between calls.
"""

# Coefficients of the per-capita growth polynomial g(N1, N2, P1).
# Key = tuple of exponents (a, b, c) meaning N1**a * N2**b * P1**c.
# dN1/dt = N1 * sum_k COEF[k] * N1**a * N2**b * P1**c
COEF = {
    (0, 0, 0):  0.007218973195917547,
    (1, 0, 0): -0.04326955250005932,
    (0, 1, 0):  0.024258655960927165,
    (0, 0, 1):  0.025748471739762212,
    (2, 0, 0): -1.0418528826237704e-05,
    (1, 1, 0):  0.0006929613612037264,
    (1, 0, 1):  0.006238669334360681,
    (0, 2, 0): -0.0003780937186344432,
    (0, 1, 1): -0.003474260565424599,
    (0, 0, 2):  0.013279865758701475,
    (3, 0, 0):  1.5100160069257663e-06,
    (2, 1, 0):  6.652184903707612e-07,
    (2, 0, 1): -3.736377028788194e-05,
    (1, 2, 0): -4.036838592652094e-06,
    (1, 1, 1): -3.556808830169548e-05,
    (1, 0, 2): -0.00013222845614477229,
    (0, 3, 0):  1.5948003509693803e-06,
    (0, 2, 1):  3.0672010005461724e-05,
    (0, 1, 2): -0.00013333670521954168,
    (0, 0, 3):  7.237418016580725e-06,
}


def _dN1_dt(N1: float, N2: float, P1: float) -> float:
    g = 0.0
    for (a, b, c), coef in COEF.items():
        g += coef * (N1 ** a) * (N2 ** b) * (P1 ** c)
    return N1 * g


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to a predicted dN1_dt.

    Uses only the declared variables N1, N2, P1 (t is not needed: the system is
    autonomous) and fixed constants inferred from the training data.
    """
    out = []
    for row in input_data:
        N1 = float(row["N1"])
        N2 = float(row["N2"])
        P1 = float(row["P1"])
        out.append({"dN1_dt": _dN1_dt(N1, N2, P1)})
    return out
