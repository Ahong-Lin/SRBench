import math


# Parameters fitted on /app/data/train_data.csv (R^2 = 0.9938).
# Model:
#   dp = a*dc + a2*dc^2 + b*dc^3          (own-signal response, mildly asymmetric cubic)
#      + c*dc*pi + h*pi                    (weight/inflation interaction with dc)
#      + d*sin(k1*dp_comp)                 (saturating competitor pass-through)
#      + e*sin(k2*dc_acc)                  (saturating acceleration term)
#      + j*dc*sigma_c                       (small volatility interaction)
#      + g                                  (offset)
A = 0.121265
A2 = 0.035448
B = 0.076135
C = 0.141139
D = 0.164007
K1 = 1.196588
E = 0.189990
K2 = 0.932040
H = 0.017858
J = -0.023660
G = -0.012698


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts `dp` from the input variables according to the discovered law.
    """
    out = []
    for row in input_data:
        dc = row["dc"]
        pi = row["pi"]
        dp_comp = row["dp_comp"]
        sigma_c = row["sigma_c"]
        dc_acc = row["dc_acc"]

        dp = (
            A * dc
            + A2 * dc * dc
            + B * dc * dc * dc
            + C * dc * pi
            + D * math.sin(K1 * dp_comp)
            + E * math.sin(K2 * dc_acc)
            + H * pi
            + J * dc * sigma_c
            + G
        )
        out.append({"dp": dp})
    return out
