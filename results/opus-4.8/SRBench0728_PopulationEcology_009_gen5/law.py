import math


# ---------------------------------------------------------------------------
# Discovered law (Gompertz growth regulated by the delayed crowding density):
#
#     dN/dt = r * N * ln(K / crowding_load)
#           = N * (A + B * ln(crowding_load))
#
# Fitted on /app/data/train_data.csv (least squares on dN/dt):
#     A =  2.039104     B = -0.299738
#     => r = -B = 0.299738 ,  K = exp(-A/B) = 900.50
#
# The companion (exactly recovered) equation for the crowding variable is
#     d(crowding_load)/dt = 0.2 * (N - crowding_load)
# i.e. crowding_load is a low-pass / delayed copy of N.  Together these two
# equations produce the observed damped oscillation converging to N = C = K.
# ---------------------------------------------------------------------------

A = 2.039104
B = -0.299738


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        N = row["N"]
        C = row["crowding_load"]
        # guard against non-positive crowding (log domain)
        c = C if C > 1e-9 else 1e-9
        dN_dt = N * (A + B * math.log(c))
        out.append({"dN_dt": dN_dt})
    return out


if __name__ == "__main__":
    import pandas as pd
    import numpy as np

    df = pd.read_csv("/app/data/train_data.csv")
    preds = law(df.to_dict("records"))
    p = np.array([d["dN_dt"] for d in preds])
    y = df["dN_dt"].values
    r2 = 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)
    print(f"train R2 = {r2:.5f}  rmse = {np.sqrt(np.mean((y-p)**2)):.4f}")
