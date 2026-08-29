"""
Discovered law for the observed dynamical system.

Target: instantaneous right-hand side dN_dt as an explicit pointwise function
of the observed state (N, crowding_load).

Model (per-capita growth form):

    dN/dt = N * g(N, C)
    g(N, C) = a + b*N + c*C + d*C^2 + e*N*C

where N is the population and C is `crowding_load`.

The per-capita growth rate g is a smooth (quadratic-order) response to the
crowding load C and the population N.  The auxiliary variable crowding_load
itself relaxes toward N (empirically dC/dt = 0.2*(N - C)), so the coupled
system produces the observed damped oscillation that converges to the
equilibrium N = C ~= 900, which is exactly where g(N, N) = 0 for these
coefficients.

Coefficients were fit by least squares on the full training trajectory.
The law is autonomous (no explicit time dependence) so it remains valid
beyond the observed time window.
"""

# Fitted parameters (least squares on train_data.csv)
A = 0.5419348179363719      # constant per-capita rate
B = -2.765497823490045e-05  # N term
C1 = -0.0007618397632202418 # crowding_load (linear) term
D = 1.5192381011835046e-07  # crowding_load^2 term
E = 5.650655476304416e-08   # N * crowding_load cross term


def _dN_dt(N: float, C: float) -> float:
    g = A + B * N + C1 * C + D * C * C + E * N * C
    return N * g


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to one dN_dt prediction."""
    out = []
    for row in input_data:
        N = float(row["N"])
        C = float(row["crowding_load"])
        out.append({"dN_dt": _dN_dt(N, C)})
    return out


if __name__ == "__main__":
    # quick self-test against training data
    import csv
    import os

    path = os.path.join(os.path.dirname(__file__), "data", "train_data.csv")
    rows, ref = [], []
    with open(path) as f:
        for r in csv.DictReader(f):
            rows.append({"N": float(r["N"]), "crowding_load": float(r["crowding_load"])})
            ref.append(float(r["dN_dt"]))
    pred = [d["dN_dt"] for d in law(rows)]
    n = len(ref)
    mean = sum(ref) / n
    ss_res = sum((p - y) ** 2 for p, y in zip(pred, ref))
    ss_tot = sum((y - mean) ** 2 for y in ref)
    print(f"n={n}  R2={1 - ss_res / ss_tot:.5f}  RMSE={(ss_res / n) ** 0.5:.3f}")
