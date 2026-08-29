"""Discovered acceleration law for the observed dynamical system.

The system behaves as a forced Duffing-type oscillator with weak
nonlinear (amplitude-dependent) damping:

    dv/dt = a1*x + a2*x^3 + a3*v + a4*Fh + a5*Fh2 + a6*x^2*v + a7*v^3

Coefficients were fit by ordinary least squares on the training set and
validated on held-out right-hand time segments (extrapolation RMSE ~7e-4).
"""

# Fitted parameters (ordinary least squares on full training set)
A_X    = -0.9976596593875134   # linear restoring force  (~ -omega^2 x)
A_X3   = -0.05324145002716377  # cubic (Duffing) stiffness
A_V    = -0.03018032117490677  # linear damping
A_FH   = -0.10393446590779072  # forcing term Fh
A_FH2  = -0.04739737965688178  # forcing term Fh2
A_X2V  =  0.0032951952570173084  # nonlinear damping x^2 * v
A_V3   = -0.010692440024353636   # nonlinear damping v^3
A_CONST = 2.6951243454836087e-05  # (negligible offset)


def _predict(row: dict) -> float:
    x = row["x"]
    v = row["v"]
    Fh = row["Fh"]
    Fh2 = row["Fh2"]
    return (
        A_X * x
        + A_X3 * x * x * x
        + A_V * v
        + A_FH * Fh
        + A_FH2 * Fh2
        + A_X2V * x * x * v
        + A_V3 * v * v * v
        + A_CONST
    )


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to a predicted dv_dt."""
    return [{"dv_dt": _predict(row)} for row in input_data]


if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    df = pd.read_csv("/app/data/train_data.csv")
    preds = [d["dv_dt"] for d in law(df.to_dict("records"))]
    err = np.array(preds) - df["dv_dt"].values
    print("train RMSE:", np.sqrt(np.mean(err ** 2)))
    print("train max abs err:", np.max(np.abs(err)))
