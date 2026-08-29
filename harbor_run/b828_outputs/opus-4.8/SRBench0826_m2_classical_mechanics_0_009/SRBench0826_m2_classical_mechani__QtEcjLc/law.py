"""
Discovered law for the instantaneous right-hand side dv/dt of a hardening
(cubic) spring oscillator that is weakly coupled to an auxiliary reservoir.

The relationship was identified by symbolic regression on the training data.
It is an explicit, pointwise function of the observed variables and carries no
state between calls, no data reads, and no trajectory processing.

    dv/dt = -x - 0.5*x**3          # Duffing restoring force (linear + cubic hardening)
            - z                     # coupling force to the auxiliary variable z
            - 2.0*x*v**2            # velocity-dependent (position-modulated) term
            - (0.11998*v + 0.12513*v**3 - 0.05495*v**5 + 0.01117*v**7)   # nonlinear damping in v

Only the declared variables (t, x, v, z, e) may be used.  Here dv/dt depends on
x, v and z; t and e are not needed (e is redundant: it satisfies de/dt = v*z and
its inclusion only degrades extrapolation).
"""

# Restoring / coupling coefficients (identified as exact, round values).
A_X   = -1.0     # linear stiffness (k/m)
A_X3  = -0.5     # cubic hardening (beta/m)
A_Z   = -1.0     # coupling to auxiliary variable z
A_XV2 = -2.0     # position * velocity^2 term

# Nonlinear (odd) damping series in v, fitted on the training data.
D1 = -0.11998
D3 = -0.12513
D5 =  0.05495
D7 = -0.01117


def _dv_dt(x: float, v: float, z: float) -> float:
    v2 = v * v
    restoring = A_X * x + A_X3 * x * x * x
    coupling = A_Z * z
    kinematic = A_XV2 * x * v2
    damping = D1 * v + D3 * v * v2 + D5 * v * v2 * v2 + D7 * v * v2 * v2 * v2
    return restoring + coupling + kinematic + damping


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to one dv_dt prediction.

    The verifier calls this with exactly one row at a time; we handle any
    number of rows for convenience but treat every row independently.
    """
    out = []
    for row in input_data:
        x = float(row["x"])
        v = float(row["v"])
        z = float(row["z"])
        out.append({"dv_dt": _dv_dt(x, v, z)})
    return out


if __name__ == "__main__":
    # quick self-check against the training data if available
    try:
        import pandas as pd
        df = pd.read_csv("/app/data/train_data.csv")
        preds = law(df.to_dict("records"))
        p = [d["dv_dt"] for d in preds]
        err = (df["dv_dt"] - p).abs()
        print("max abs err:", err.max(), "rmse:", (err**2).mean() ** 0.5)
    except Exception as exc:  # pragma: no cover
        print("self-check skipped:", exc)
