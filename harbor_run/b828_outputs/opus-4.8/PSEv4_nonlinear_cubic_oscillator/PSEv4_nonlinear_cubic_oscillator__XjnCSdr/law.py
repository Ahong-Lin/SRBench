"""Discovered law for dv_dt.

Model (damped cubic / Duffing-type oscillator with amplitude-dependent damping):

    dv/dt = -a * x**3  -  (b - m*|x| - n*x**2) * v

where the restoring force is a pure cubic spring (-a x^3) and the damping
coefficient decreases with displacement magnitude.

Parameters were inferred from /app/data/train_data.csv:
    a = 2.25049505      (restoring; ~= 9/4, confirmed at turning points v~0)
    b = 0.69869719      (damping at x = 0, confirmed on the x~0 slice)
    m = 0.18463584      (linear |x| reduction of damping)
    n = 0.03992012      (quadratic x^2 reduction of damping)

Fit quality on training data: R^2 = 0.9999999, RMSE = 1.2e-4.
"""

A = 2.25049505
B = 0.69869719
M = 0.18463584
N = 0.03992012


def _dv_dt(x: float, v: float) -> float:
    damping_coeff = B - M * abs(x) - N * x * x
    return -A * x ** 3 - damping_coeff * v


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to a dv_dt prediction.

    Uses only the declared variables x and v (t is not needed: the RHS is
    autonomous). Returns a list of one dict {'dv_dt': value} per input row.
    """
    out = []
    for row in input_data:
        x = float(row["x"])
        v = float(row["v"])
        out.append({"dv_dt": _dv_dt(x, v)})
    return out
