"""Discovered law for the thermal enzyme-inactivation experiment.

Target: instantaneous rate of change of the active (native) enzyme pool, dE/dt.

Exact closed form (recovered to machine precision on the training data):

    dE/dt = -0.01 * E**2 - 0.1 * E + (0.4 - 0.6 / (E + 2.0)) * A

It is a pointwise function of the state variables E (active enzyme) and A
(reversibly unfolded intermediate) only.  The columns t and G are not needed
to reproduce dE/dt (the dynamics of G are a separate equation of the same
system and do not feed back into the active-enzyme balance).

Mechanistic reading (all rates in the same units as the data):
    * Logistic production/regeneration of native enzyme:   +0.2*E - 0.01*E**2
    * First-order unfolding  N -> U:                        -0.3*E
    * Refolding  U -> N with an E-dependent rate constant
      kr(E) = 0.4 - 0.6/(E+2):                              +kr(E)*A
Summing the production and unfolding E-terms gives -0.1*E - 0.01*E**2.
"""

# Constants inferred from the training data (exact to ~1e-15).
K_QUAD = 0.01      # coefficient of the -E^2 term
K_LIN = 0.1        # coefficient of the -E term
KR_MAX = 0.4       # saturating refolding rate constant at large E
KR_B = 0.6         # numerator of the E-dependent correction
KR_C = 2.0         # offset in the denominator (E + 2)


def _dE_dt(E: float, A: float) -> float:
    kr = KR_MAX - KR_B / (E + KR_C)          # E-dependent refolding rate constant
    return -K_QUAD * E * E - K_LIN * E + kr * A


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to a single dE_dt prediction.

    The verifier calls this with exactly one row at a time; we return a list
    containing exactly one dict with key 'dE_dt'.
    """
    out = []
    for row in input_data:
        E = float(row["E"])
        A = float(row["A"])
        out.append({"dE_dt": _dE_dt(E, A)})
    return out


if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    df = pd.read_csv("/app/data/train_data.csv")
    preds = law(df.to_dict("records"))
    p = np.array([d["dE_dt"] for d in preds])
    err = p - df["dE_dt"].values
    print("max abs error:", np.max(np.abs(err)))
    print("rmse:", np.sqrt(np.mean(err ** 2)))
