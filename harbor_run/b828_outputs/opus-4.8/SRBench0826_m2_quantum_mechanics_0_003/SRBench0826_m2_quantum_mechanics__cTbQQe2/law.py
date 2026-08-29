"""Discovered law for the excited-state population rate dP_dt.

    dP_dt = 0.4 * C - 0.4 * P - 0.3 * P**2

Fits the training data to machine precision (max abs error ~1.5e-16).
See explain.md for the full derivation and interpretation.
"""

# Fixed constants inferred from the training data.
A_C = 0.4   # coupling gain on the coherence term C
A_P = 0.4   # linear decay/relaxation on P
A_P2 = 0.3  # nonlinear (saturation) term on P


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    P = row["P"]
    C = row["C"]
    dP_dt = A_C * C - A_P * P - A_P2 * P * P
    return [{"dP_dt": dP_dt}]
