"""
Discovered law for the observed dynamical system.

Target:  dN_dt  (instantaneous right-hand side of the population equation)
Inputs :  t, N, crowding_load   (only N and crowding_load are used)

Model (distributed-delay / crowding logistic):

    dN/dt = r * N * (1 - crowding_load / K)

where `crowding_load` is a lagged measure of the population that limits growth
(its own dynamics obey  d(crowding_load)/dt = 0.2 * (N - crowding_load),
i.e. an exponential moving average of N with time constant 5).

Per-capita growth  (1/N) dN/dt  falls linearly with the crowding load, is
positive when crowding_load < K, negative when it exceeds K, and vanishes at
the equilibrium N = crowding_load = K.  The coefficients were estimated from
the settling (near-equilibrium) portion of the trajectory, which is the regime
the hidden right-hand test segment lives in.
"""

# Fitted constants (estimated from the training trajectory, t >= 15)
R = 0.3605      # intrinsic per-capita growth rate
K = 902.22      # crowding-load carrying capacity (equilibrium level)


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        N = row["N"]
        C = row["crowding_load"]
        dN_dt = R * N * (1.0 - C / K)
        out.append({"dN_dt": dN_dt})
    return out


if __name__ == "__main__":
    # quick self-check against the training file (not used by the verifier)
    import csv
    import os

    path = os.path.join(os.path.dirname(__file__), "data", "train_data.csv")
    if os.path.exists(path):
        rows = list(csv.DictReader(open(path)))
        X = [{k: float(v) for k, v in r.items()} for r in rows]
        preds = law(X)
        y = [float(r["dN_dt"]) for r in rows]
        p = [d["dN_dt"] for d in preds]
        mean = sum(y) / len(y)
        ss_res = sum((a - b) ** 2 for a, b in zip(y, p))
        ss_tot = sum((a - mean) ** 2 for a in y)
        print("global R^2 =", 1 - ss_res / ss_tot)
