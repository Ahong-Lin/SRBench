"""Discovered law for kinase active-fraction vs stimulus (Hill / cooperative activation).

A(X) = A0 + (Amax - A0) * X**n / (K**n + X**n)

A leaky Hill function: a basal active fraction A0 at low stimulus, rising through a
switch-like transition at X ~ K with cooperativity (Hill coefficient) n, and
saturating at Amax for high stimulus.
"""

# Parameters fitted to the clean training signal (train_data.csv, column A).
AMAX = 0.8354728507907402   # saturating active fraction at high stimulus
K = 6.150231859905276       # half-activation stimulus level (X at midpoint)
N = 1.797914327796835       # Hill coefficient (cooperativity / sharpness)
A0 = 0.055900173430713726   # basal active fraction at low stimulus


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    X = row["X"]
    xn = X ** N
    A = A0 + (AMAX - A0) * xn / (K ** N + xn)
    return [{"A": A}]
