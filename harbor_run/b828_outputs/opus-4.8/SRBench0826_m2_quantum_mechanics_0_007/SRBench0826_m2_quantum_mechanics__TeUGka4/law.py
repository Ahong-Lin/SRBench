"""Discovered law for coherent double-well tunneling.

    dPr_dt = K * N + gamma * (Pr_eq - Pr)

with gamma = 0.1 and Pr_eq = 0.5.

Interpretation:
  * K * N  is the coherent tunneling drive: the coherence-like variable K
    multiplied by the (slowly decaying) amplitude/norm factor N transfers
    probability back and forth between the two wells.
  * gamma * (0.5 - Pr) is a relaxation term pulling the population toward the
    equally-shared equilibrium Pr = 0.5 at rate gamma = 0.1 (decoherence /
    damping of the oscillation amplitude seen in the data).

Fitted on the training set to machine precision (max abs residual ~1.7e-16).
"""

GAMMA = 0.1      # relaxation rate toward equilibrium
PR_EQ = 0.5      # equilibrium population (equal sharing between wells)


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        Pr = row["Pr"]
        K = row["K"]
        N = row["N"]
        dPr_dt = K * N + GAMMA * (PR_EQ - Pr)
        out.append({"dPr_dt": dPr_dt})
    return out
