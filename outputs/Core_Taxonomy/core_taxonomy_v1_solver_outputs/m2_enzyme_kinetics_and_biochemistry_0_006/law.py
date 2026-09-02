"""Discovered law for enzyme turnover rate A as a function of pH and Temp.

Bell-shaped pH dependence (diprotic catalytic model) with a temperature-dependent
shift of the two ionization constants:

    A = b + amp / (1 + 10^(pKa1(T) - pH) + 10^(pH - pKa2(T)))

where
    pKa1(T) = pKa1_0 + c * (T - 300)
    pKa2(T) = pKa2_0 + c * (T - 300)

Fitted on /app/data/train_data.csv (R^2 = 0.99987).
"""

# Fitted parameters
B       = 7.99838607      # baseline activity floor
AMP     = 91.89728760     # bell amplitude
PKA1_0  = 6.03661159      # acidic-side pKa at 300 K
PKA2_0  = 8.04093405      # basic-side pKa at 300 K
C       = 0.02329917660   # pKa temperature shift (per K), same for both groups
T_REF   = 300.0


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    pH = row["pH"]
    T = row["Temp"]

    dT = T - T_REF
    pka1 = PKA1_0 + C * dT
    pka2 = PKA2_0 + C * dT

    denom = 1.0 + 10.0 ** (pka1 - pH) + 10.0 ** (pH - pka2)
    A = B + AMP / denom
    return [{"A": A}]
