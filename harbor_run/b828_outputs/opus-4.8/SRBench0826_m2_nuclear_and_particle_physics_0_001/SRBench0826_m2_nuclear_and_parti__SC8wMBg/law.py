"""
Discovered law for the instantaneous daughter-population rate dNd/dt in a
parent -> daughter -> stable decay chain.

Target (pointwise, per-row):

    dNd_dt = -LAMBDA_D * Nd  +  Np * C(Nd/Np)

where the daughter's intrinsic decay constant is

    LAMBDA_D = 0.05

and C(h) is the (bounded, rational) *effective parent-coupling* term written as a
function of the dimensionless ratio  h = Nd/Np :

    C(h) = (a + b*h + c*h**2) / (1 + d*h + e*h**2)

C(h) is positive at early times (small h, large parent stock -> net production of
the daughter) and saturates to a small constant   c/e ~= -0.076   at late times
(large h), so that asymptotically

    dNd_dt  ->  -0.05*Nd - 0.076*Np      (parent negligible: pure decay of Nd)

Only the declared variables t, Np, Nd are available; the relation actually uses
Np and Nd (t is redundant here because Np = 10000*exp(-0.1*t) exactly on this
experiment).  All numbers below are fixed constants inferred from the training
data.  Each input row is mapped independently to a single dNd_dt value.
"""

# Intrinsic daughter decay constant (clean asymptotic value from the late-time tail)
LAMBDA_D = 0.05

# Rational effective-coupling coefficients C(h) = (a + b h + c h^2)/(1 + d h + e h^2)
A = 0.0683939720585721        # C(0): exact production coefficient at t=0 (Nd=0)
B = -0.018544198058948524
C2 = -0.004083425555820339
D = 0.12409373465490975
E = 0.05346669086691867

# Asymptotic (large-h) value of C, used as a safe fallback when Np -> 0
C_INF = C2 / E                 # ~= -0.07637


def _predict(t, Np, Nd):
    # Guard the vanishing-parent limit (Np ~ 0): h -> inf, C(h) -> C_INF.
    if Np <= 1e-300:
        return -LAMBDA_D * Nd + Np * C_INF

    h = Nd / Np
    num = A + B * h + C2 * h * h
    den = 1.0 + D * h + E * h * h
    C = num / den
    return -LAMBDA_D * Nd + Np * C


def law(input_data):
    """Map each input row independently to one dNd_dt prediction.

    Parameters
    ----------
    input_data : list[dict[str, float]]
        Each dict has keys 't', 'Np', 'Nd'.

    Returns
    -------
    list[dict[str, float]]
        One dict {'dNd_dt': value} per input row.
    """
    out = []
    for row in input_data:
        t = row.get("t", 0.0)
        Np = row["Np"]
        Nd = row["Nd"]
        out.append({"dNd_dt": _predict(t, Np, Nd)})
    return out
