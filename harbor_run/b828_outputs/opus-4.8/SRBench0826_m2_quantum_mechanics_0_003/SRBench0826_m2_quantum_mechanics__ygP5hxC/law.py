"""Discovered law for the two-level (Rabi/Bloch) population-transfer dataset.

Target:  dP_dt = 0.4 * C - 0.4 * P - 0.3 * P**2

Discovered by sparse polynomial (SINDy-style) regression over the candidate
library {t, P, C, W, N and their pairwise products}.  Only three terms are
required; the fit reproduces the training target to machine precision
(max |error| ~ 1.5e-16).  The variables t, W and N do not enter the
right-hand side.
"""

# Fixed constants inferred from the training data (exact to double precision).
A_COH = 0.4   # coherent drive / gain proportional to the coherence C
A_LIN = 0.4   # linear relaxation of the excited-state population P
A_SAT = 0.3   # nonlinear (saturation) self-coupling term in P


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to one dP_dt prediction.

    dP_dt = A_COH * C - A_LIN * P - A_SAT * P**2
    """
    out = []
    for row in input_data:
        P = row["P"]
        C = row["C"]
        dP_dt = A_COH * C - A_LIN * P - A_SAT * P * P
        out.append({"dP_dt": dP_dt})
    return out


if __name__ == "__main__":
    # quick self-check against the training file when run directly
    import csv
    import os

    path = os.path.join(os.path.dirname(__file__), "data", "train_data.csv")
    rows, ref = [], []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append({k: float(r[k]) for k in ("t", "P", "C", "W", "N")})
            ref.append(float(r["dP_dt"]))
    pred = law(rows)
    err = max(abs(p["dP_dt"] - y) for p, y in zip(pred, ref))
    print(f"max abs error on training set: {err:.3e}")
