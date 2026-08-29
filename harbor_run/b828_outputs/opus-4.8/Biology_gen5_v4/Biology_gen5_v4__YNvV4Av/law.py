import math


# ---------------------------------------------------------------------------
# Discovered law for the circadian output variable X(t, I_light_prev)
#
#   X = A(I) * sin(w*t + phi)
#       + a2*cos(2*w*t) + b2*sin(2*w*t)      (fixed 2nd harmonic)
#       + b3*sin(3*w*t)                       (fixed 3rd harmonic)
#
# where the fundamental amplitude is a light-driven saturating (Hill) term:
#
#   A(I) = c + V * I^n / (K^n + I^n)
#
# The oscillation period 2*pi/w ~= 23.95 (a ~24 h circadian rhythm).
# Previous light intensity `I_light_prev` boosts the fundamental amplitude
# from a baseline c (dark) toward a saturated maximum c + V, while the
# higher harmonics that shape the waveform are light-independent.
# ---------------------------------------------------------------------------

# Fitted parameters (least-squares on the training set, R^2 ~= 0.983)
W = 0.26236687876119685
PHI = -0.018946795783345502
C = 0.8136337854243837
V = 0.7928491192931701
K = 0.7930343004049694
N = 5.1980634219686355
A2 = -0.29756023929433856
B2 = 0.0625444271635387
B3 = -0.05406907680291444


def _predict(t: float, I: float) -> float:
    # Saturating (Hill) amplitude driven by previous light intensity.
    if I <= 0.0:
        amp = C
    else:
        hill = I ** N / (K ** N + I ** N)
        amp = C + V * hill

    x = amp * math.sin(W * t + PHI)
    x += A2 * math.cos(2.0 * W * t) + B2 * math.sin(2.0 * W * t)
    x += B3 * math.sin(3.0 * W * t)
    return x


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the output variable based on the input variables according to a
    discovered law.
    """
    results = []
    for row in input_data:
        t = float(row["t"])
        I = float(row["I_light_prev"])
        results.append({"X": _predict(t, I)})
    return results


if __name__ == "__main__":
    import pandas as pd

    df = pd.read_csv("/app/data/train_data.csv")
    preds = law(df[["t", "I_light_prev"]].to_dict("records"))
    p = [d["X"] for d in preds]
    import numpy as np

    p = np.array(p)
    y = df["X"].values
    r2 = 1 - np.sum((y - p) ** 2) / np.sum((y - y.mean()) ** 2)
    print("R^2 =", r2)
