"""Discovered law for coherent double-well tunneling.

    dPr_dt = K * N + kappa * (0.5 - Pr)

with kappa = 0.1 (a fixed relaxation rate inferred from the training data).

Interpretation
--------------
* ``K * N`` is the coherent tunneling current: the product of the coherence
  channel ``K`` and the envelope factor ``N`` produces the reversible
  back-and-forth transfer of probability between the two wells.
* ``kappa * (0.5 - Pr)`` is a linear relaxation term that drives the
  occupation probability toward the symmetric equilibrium value 1/2.

The relationship is pointwise (each row maps independently to one prediction)
and reproduces the training targets to machine precision (max |err| ~ 2e-16).
Note that ``t`` and ``J`` do not appear: the instantaneous right-hand side is
fully determined by ``Pr``, ``K`` and ``N``.
"""

KAPPA = 0.1  # relaxation rate toward equilibrium occupation 1/2


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        Pr = row["Pr"]
        K = row["K"]
        N = row["N"]
        dPr_dt = K * N + KAPPA * (0.5 - Pr)
        out.append({"dPr_dt": dPr_dt})
    return out
