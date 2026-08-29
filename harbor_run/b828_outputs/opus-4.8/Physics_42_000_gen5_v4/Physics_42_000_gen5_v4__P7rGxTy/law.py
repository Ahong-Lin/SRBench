import math


# Discovered law: the settling velocity is a sum of three exponential
# relaxation modes approaching a terminal velocity.
#   v(t) = v_inf - a1*exp(-k1*t) - a2*exp(-k2*t) - a3*exp(-k3*t)
# Parameters fitted to the training data (RMSE ~8e-7).
V_INF = 10.792247701102658
A1, K1 = 8.796514582503484, 0.9760873841147891
A2, K2 = 5.4869336166966285, 0.4948003200972703
A3, K3 = -3.57730809873561, 1.5472214146061483


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the settling velocity v from time t.

    v(t) = V_INF - A1*exp(-K1*t) - A2*exp(-K2*t) - A3*exp(-K3*t)
    """
    out = []
    for row in input_data:
        t = row["t"]
        v = (
            V_INF
            - A1 * math.exp(-K1 * t)
            - A2 * math.exp(-K2 * t)
            - A3 * math.exp(-K3 * t)
        )
        out.append({"v": v})
    return out
