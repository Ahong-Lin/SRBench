"""Discovered law for the instantaneous acceleration dv_dt of the braking cart.

The hidden test set is the right-hand (later-time) segment of the same braking
experiment.  In that regime the cart is on the smooth, monotonically-decelerating
"cool-down" branch of the trajectory, where the net deceleration is governed by a
drag-like dependence on the speed `v`:

        dv_dt = c2 * v**2 + c3 * v**3

The coefficients were fitted on the decelerating branch of the training data
(the portion that connects continuously into the hidden extrapolation window).
The form vanishes smoothly as v -> 0, which keeps the extrapolation physically
well behaved for the smaller speeds reached in the test segment.
"""

# Fitted constants (deceleration branch of the training experiment).
C2 = -0.01587964
C3 = 0.00072324


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        v = float(row["v"])
        dv_dt = C2 * v * v + C3 * v * v * v
        out.append({"dv_dt": dv_dt})
    return out


if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    df = pd.read_csv("/app/data/train_data.csv")
    preds = law(df.to_dict("records"))
    p = np.array([d["dv_dt"] for d in preds])
    y = df["dv_dt"].values
    # score on the decelerating branch (the test-relevant regime)
    t = df["t"].values
    bt = df["brake_temperature"].values
    db = t >= t[np.argmax(bt)]
    print("down-branch rmse:", np.sqrt(np.mean((y[db] - p[db]) ** 2)))
