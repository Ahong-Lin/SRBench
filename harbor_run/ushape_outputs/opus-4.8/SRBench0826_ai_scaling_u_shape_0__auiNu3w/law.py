import math

# Discovered law:
#   Brier(logC) = cubic baseline + sum of localized Gaussian "bumps"
#   baseline(x) = c0 + c1*x + c2*x^2 + c3*x^3
#   bump_k(x)   = A_k * exp(-(x-mu_k)^2 / (2*s_k^2))
# Fitted on /app/data/train_data.csv (noise-free, 4500 pts).

C = (0.1234196, -0.002267291, 0.02830533, 0.004564549)
GAUSS = (
    (0.1688701,  -1.015833,  0.3394543),
    (0.06220959, -0.5900829, 0.6440599),
    (0.006146539, 0.6979127, 0.2684551),
    (-0.02314605, -0.2891183, 0.3357512),
    (0.04830997,  1.840273,  0.4638322),
)


def _predict(x: float) -> float:
    v = C[0] + C[1] * x + C[2] * x * x + C[3] * x ** 3
    for A, mu, s in GAUSS:
        v += A * math.exp(-((x - mu) ** 2) / (2.0 * s * s))
    return v


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Return one {"Brier": value} prediction for every input row."""
    return [{"Brier": _predict(float(row["logC"]))} for row in input_data]
