"""
Discovered law for predicting X from the experimental dataset.

Summary of the analysis (see explain.md for full details):

  * `X` is a deterministic function of the time variable `t` only.
  * `I_light_prev` is uniform white noise on [0, 2], uncorrelated with `X`
    at every lag (|corr| < 0.06) and adds no predictive value. It is a
    distractor input and is intentionally ignored by the law.
  * X(t) is the sum of three oscillatory components plus an offset:
        - a slow TRANSIENT damped oscillation (period ~24.4, decays with
          time-constant tau ~29.3), i.e. the system relaxing from its
          initial condition;
        - a persistent oscillation of period ~12.15 (~2x the slow freq);
        - a persistent oscillation of period ~5.07;
        - a constant baseline.

  Fit quality on the training set: R^2 = 0.991. The model extrapolates in
  time (fit on the first 60% predicts the last 40% with residual std ~0.02),
  confirming it is a genuine function of t rather than a memorised curve.
"""

from math import exp, cos

# Parameters fit by non-linear least squares on /app/data/train_data.csv.
# X(t) = A1 * exp(-t/tau1) * cos(w1*t + p1)   # decaying transient
#      + Aa * cos(wa*t + pa)                   # persistent mode (period ~12.15)
#      + Ab * cos(wb*t + pb)                   # persistent mode (period ~5.07)
#      + c
A1, tau1, w1, p1 = 2.229699, 29.311118, 0.257253, -0.782699
Aa, wa, pa = 0.153439, 0.517307, -0.727749
Ab, wb, pb = 0.258192, 1.240254, -3.583885
c = 0.071281


def _predict(t: float) -> float:
    return (
        A1 * exp(-t / tau1) * cos(w1 * t + p1)
        + Aa * cos(wa * t + pa)
        + Ab * cos(wb * t + pb)
        + c
    )


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Predict X for each input row.

    Each element of `input_data` is a dict that contains at least the key
    `t` (and typically `I_light_prev`, which is ignored). Returns a list of
    dicts `{"X": <prediction>}` in the same order.
    """
    out = []
    for row in input_data:
        t = float(row["t"])
        out.append({"X": _predict(t)})
    return out


if __name__ == "__main__":
    import pandas as pd

    d = pd.read_csv("/app/data/train_data.csv")
    preds = [p["X"] for p in law(d.to_dict("records"))]
    import numpy as np

    x = d["X"].values
    pr = np.array(preds)
    r2 = 1 - np.sum((x - pr) ** 2) / np.sum((x - x.mean()) ** 2)
    print(f"train R^2 = {r2:.5f}  resid std = {(x - pr).std():.5f}")
