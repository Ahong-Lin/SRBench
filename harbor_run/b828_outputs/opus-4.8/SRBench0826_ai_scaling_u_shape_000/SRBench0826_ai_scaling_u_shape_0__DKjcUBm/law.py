import math

# Discovered closed-form law for Brier as a function of logC.
#
#   Brier(x) = a3*x^3 + a2*x^2 + a1*x + a0            (smooth cubic scaling trend)
#            + A1*sin(w1*x + p1) + A2*sin(w2*x + p2)  (two-tone periodic ripple)
#            + Ag*exp(-(x-mu)^2 / (2*s^2))            (localized Gaussian bump)
#
# where x = logC. Parameters fitted by non-linear least squares on the
# training data (RMSE ~2.7e-4, max abs error ~1.4e-3).

A3 =  0.00239481
A2 =  0.02827727
A1 =  0.01657230
A0 =  0.13544945

SIN1_A =  0.01298341
SIN1_W =  3.19871937
SIN1_P =  1.84323209

SIN2_A = -0.00266075
SIN2_W =  5.50779119
SIN2_P =  1.09103988

G_A  =  0.23706361
G_MU = -1.00843334
G_S  =  0.35949227


def _brier(x: float) -> float:
    trend = A3 * x**3 + A2 * x**2 + A1 * x + A0
    ripple = (SIN1_A * math.sin(SIN1_W * x + SIN1_P)
              + SIN2_A * math.sin(SIN2_W * x + SIN2_P))
    bump = G_A * math.exp(-((x - G_MU) ** 2) / (2.0 * G_S ** 2))
    return trend + ripple + bump


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Return one {"Brier": value} prediction for every input row."""
    out = []
    for row in input_data:
        x = float(row["logC"])
        out.append({"Brier": _brier(x)})
    return out
