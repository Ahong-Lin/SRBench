"""Discovered law for the coherent population-transfer experiment.

The instantaneous right-hand side is an exact pointwise function of the
excited-state population `P` and the coherence variable `C`:

    dP_dt = 0.4 * C - 0.4 * P - 0.3 * P**2

Coefficients were recovered to machine precision from the training data
(least-squares residual ~2e-16, R^2 = 1.0). Only the declared per-row
variables are used; no state is carried between calls.
"""

# Fixed constants inferred from the training data.
A = 0.4   # coupling / coherent-transfer gain on C
B = 0.4   # linear decay of P
D = 0.3   # quadratic (saturation) term in P


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        P = row["P"]
        C = row["C"]
        dP_dt = A * C - B * P - D * P * P
        out.append({"dP_dt": dP_dt})
    return out
