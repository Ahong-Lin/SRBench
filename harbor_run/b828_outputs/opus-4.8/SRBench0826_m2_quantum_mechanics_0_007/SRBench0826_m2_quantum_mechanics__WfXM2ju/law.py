"""Discovered law for coherent tunneling oscillation between two wells.

The instantaneous rate of change of the occupation probability of the
initially-unoccupied well is

    dPr_dt = N * K - GAMMA_HALF * (2 * Pr - 1)

where:
  * N * K            is the coherent tunneling current. K is the (dimensionless)
                     inter-well coherence that drives population back and forth,
                     modulated by the slowly-varying envelope/number factor N.
  * -GAMMA_HALF*(2Pr-1)  is a linear relaxation term that pushes the population
                     imbalance z = 2*Pr - 1 toward equilibrium (Pr = 1/2),
                     i.e. incoherent damping of the tunneling oscillation.

Fitted from the training data to machine precision (max abs error ~1e-16):
    coefficient on (N*K)      = 1.0
    coefficient on (2*Pr - 1) = -0.05   -> GAMMA_HALF = 0.05  (relaxation rate 0.1)
"""

GAMMA_HALF = 0.05  # half the population relaxation rate driving Pr -> 1/2


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        Pr = row["Pr"]
        K = row["K"]
        N = row["N"]
        dPr_dt = N * K - GAMMA_HALF * (2.0 * Pr - 1.0)
        out.append({"dPr_dt": dPr_dt})
    return out
