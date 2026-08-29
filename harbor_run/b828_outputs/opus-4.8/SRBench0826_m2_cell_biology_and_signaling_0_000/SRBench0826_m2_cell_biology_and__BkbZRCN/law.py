"""Discovered growth law for a contact-inhibited mammalian cell population.

The instantaneous right-hand side dN/dt is modelled as a generalized-logistic
(Richards / theta-logistic) function of the current cell count N:

    dN/dt = r * N * ( 1 - (N / K)^nu )

where
    r  = intrinsic per-capita growth rate at low density,
    K  = maximum confluent (carrying) density,
    nu = shape exponent (< 1 => growth slows early and decays slowly as the
         dish approaches confluence, i.e. an asymmetric approach to K).

This form encodes the biology described: cells proliferate nearly exponentially
while space is available and division slows as the remaining free fraction
1 - (N/K)^nu shrinks toward zero at confluence.

Parameters were fit to the training trajectory.  The auxiliary observed
variables S and A (which obey their own discovered dynamics, see explain.md)
do not improve out-of-sample prediction beyond N on this experiment, and
including them degrades extrapolation into the held-out right-hand segment, so
the submitted law is a pure pointwise function of N.
"""

# Constants inferred from the training data (full-trajectory least-squares fit).
R = 0.08436579453      # intrinsic per-capita growth rate  [1/time]
K = 49298.61346        # maximum confluent density (carrying capacity) [cells]
NU = 0.2393498501      # Richards shape exponent (dimensionless)


def _dN_dt(N: float) -> float:
    return R * N * (1.0 - (N / K) ** NU)


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map one input row to one dN_dt prediction.

    Each row is handled independently; only the declared variable N is used
    together with fixed constants inferred from the training data.
    """
    row = input_data[0]
    N = row["N"]
    return [{"dN_dt": _dN_dt(N)}]
