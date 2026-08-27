"""Discovered law for contact-inhibited cell proliferation.

Model: theta-logistic (Richards) growth
    dN/dt = r * N * (1 - (N / K)^theta)

Rationale
---------
The dish has a fixed attachment surface, so division slows as the culture
approaches a maximum confluent density K. The per-capita growth rate
(dN/dt)/N falls monotonically from ~r toward 0 as N -> K. A plain logistic
(theta = 1) captures the shape only roughly (R^2 ~ 0.91); the data are
markedly skewed so that the rate stays high until the dish is quite full and
then collapses -- exactly the behaviour of the generalized-logistic / Richards
model with a shape exponent theta < 1.

The auxiliary columns S (occupied area) and A (available space per cell) were
examined but rejected as predictors: along this single growth trajectory they
are collinear with N, and A in particular is almost constant (~2.0-2.2) in the
late-time regime that the held-out test segment covers, so A-based models
(Monod / power-law in A) extrapolate very poorly (test R^2 << 0). The
theta-logistic law in N alone extrapolates cleanly to the later time segment
(80/20 forward hold-out test R^2 ~ 0.987).

Fitted parameters (full training set):
    r     = 0.0843658   (intrinsic per-capita rate, 1/time)
    K     = 49298.61     (carrying capacity / max confluent count)
    theta = 0.2393498    (Richards shape exponent)
Full-set R^2 = 0.9981.
"""

R = 0.08436581668778248
K = 49298.613691313076
THETA = 0.23934977734464255


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        N = float(row["N"])
        # theta-logistic (Richards) growth
        dN_dt = R * N * (1.0 - (N / K) ** THETA)
        out.append({"dN_dt": dN_dt})
    return out


if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("/app/data/train_data.csv")
    preds = law(df.to_dict("records"))
    p = [d["dN_dt"] for d in preds]
    y = df["dN_dt"].values
    import numpy as np

    r2 = 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)
    print("train R2:", r2)
