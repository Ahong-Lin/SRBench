import math


# Parameters fitted to /app/data/train_data.csv (see explain.md).
# Model: v(t) = V_inf * (1 - exp(-(k*t)**p))
V_INF = 10.66008065
K = 0.62797004
P = 1.03739454


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the settling velocity v of a sphere as a function of time t.

    Discovered law (stretched / compressed exponential relaxation toward the
    terminal velocity):

        v(t) = V_inf * (1 - exp(-(k * t) ** p))

    Args:
        input_data: list of dicts, each with key 't'.

    Returns:
        list of dicts, each with key 'v'.
    """
    out = []
    for row in input_data:
        t = float(row["t"])
        # (k*t)**p is only real for t >= 0; the data domain is t > 0.
        if t <= 0.0:
            v = 0.0
        else:
            v = V_INF * (1.0 - math.exp(-((K * t) ** P)))
        out.append({"v": v})
    return out
