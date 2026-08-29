"""Discovered acceleration law for the observed dynamical system.

dv/dt = c0 + c1*x + c3*x^3 + cv*v + cv3*v^3 + cFh*Fh + cFh2*Fh2

This is a driven Duffing-type oscillator: a linear + cubic restoring force
in the position x, plus a (mostly linear with a small cubic) velocity damping,
plus two externally supplied force channels Fh and Fh2 entering linearly.
Parameters were fit by linear least squares on the training data.
"""

# Fitted parameters (least squares on /app/data/train_data.csv)
C0   =  4.31503106e-05   # constant offset (~0)
C1   = -9.97628219e-01   # linear restoring (x)  ~ -1
C3   = -5.32921667e-02   # cubic restoring (x^3)
CV   = -2.73917997e-02   # linear damping (v)
CV3  = -1.34229897e-02   # cubic damping (v^3)
CFH  = -1.03226824e-01   # external force channel Fh
CFH2 = -5.04725920e-02   # external force channel Fh2


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        x = row["x"]
        v = row["v"]
        Fh = row["Fh"]
        Fh2 = row["Fh2"]
        dv_dt = (
            C0
            + C1 * x
            + C3 * x ** 3
            + CV * v
            + CV3 * v ** 3
            + CFH * Fh
            + CFH2 * Fh2
        )
        out.append({"dv_dt": dv_dt})
    return out


if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    df = pd.read_csv("/app/data/train_data.csv")
    preds = [d["dv_dt"] for d in law(df.to_dict("records"))]
    err = np.array(preds) - df["dv_dt"].values
    print("RMSE", np.sqrt(np.mean(err ** 2)), "max", np.max(np.abs(err)))
