import math


# Parameters fitted on /app/data/train_data.csv
# v(t) = A * (1 - exp(-(t/tau)^p)) - B * exp(-t/tau2)
A = 10.615274557252002
TAU = 1.5817764079068823
P = 1.049635344145202
B = -0.11771479821922361
TAU2 = 0.2926912614507756


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the settling velocity `v` from time `t`.

    Discovered law (stretched-exponential relaxation to terminal velocity
    plus a fast transient from added-mass / history force):

        v(t) = A * (1 - exp(-(t/tau)^p)) - B * exp(-t/tau2)
    """
    out = []
    for row in input_data:
        t = float(row["t"])
        main = A * (1.0 - math.exp(-((t / TAU) ** P)))
        transient = B * math.exp(-t / TAU2)
        out.append({"v": main - transient})
    return out
