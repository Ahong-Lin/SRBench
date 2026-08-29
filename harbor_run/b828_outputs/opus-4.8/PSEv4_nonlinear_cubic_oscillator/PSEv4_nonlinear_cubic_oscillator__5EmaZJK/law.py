"""Discovered law for dv_dt.

The system is a Duffing-type oscillator with a purely cubic (hardening)
restoring force and a viscous damping whose coefficient decreases with the
displacement magnitude |x|:

    dv_dt = -a * x**3  -  gamma(x) * v
    gamma(x) = b - c*|x| - d*|x|**3

with the parameters inferred from the training data:

    a = 2.25   (restoring stiffness, = 9/4)
    b = 0.70   (damping at x = 0)
    c = 0.20   (linear |x| reduction of damping)
    d = 0.025  (cubic |x| correction of damping)

Fit quality on the training set: R^2 = 0.9999997, max abs error ~1.7e-3.
The relationship uses only the declared variables x and v (t does not enter),
maps each row independently, and carries no state between calls.
"""

A = 2.25
B = 0.70
C = 0.20
D = 0.025


def _dv_dt(x: float, v: float) -> float:
    ax = abs(x)
    gamma = B - C * ax - D * ax ** 3
    return -A * x ** 3 - gamma * v


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        x = float(row["x"])
        v = float(row["v"])
        out.append({"dv_dt": _dv_dt(x, v)})
    return out
