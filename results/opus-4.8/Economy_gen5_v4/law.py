import numpy as np


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dp from (dc, pi, dp_comp, sigma_c, dc_acc) using a state-dependent
    ((S,s)-style) pricing law:

        t   = T0 - T1 * pi                      # inflation shrinks the inaction band
        dp  = K * sign(dc) * relu(|dc| - t)**P  # price adjusts only outside the band
              + A_c  * tanh(B_c  * dp_comp)      # competitor spillover
              + A_a  * tanh(B_a  * dc_acc)       # accumulated cost pass-through
              + C0
    """
    K, T0, T1, P = 0.4403, 0.5141, 0.3556, 1.1532
    A_c, B_c = 0.2025, 0.9882
    A_a, B_a = 0.2002, 0.9954
    C0 = 0.0257

    out = []
    for r in input_data:
        dc = float(r["dc"]); pi = float(r["pi"])
        dpc = float(r["dp_comp"]); acc = float(r["dc_acc"])
        t = T0 - T1 * pi
        pos = max(dc - t, 0.0)
        neg = max(-dc - t, 0.0)
        band = K * (pos ** P - neg ** P)
        val = band + A_c * np.tanh(B_c * dpc) + A_a * np.tanh(B_a * acc) + C0
        out.append({"dp": float(val)})
    return out
