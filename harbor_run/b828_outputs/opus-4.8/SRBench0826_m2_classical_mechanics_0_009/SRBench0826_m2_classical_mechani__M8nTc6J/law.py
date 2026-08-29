"""Discovered law for the instantaneous acceleration dv_dt.

The dataset is a hardening (Duffing-type) oscillator with an internal
force variable `z`, a velocity-quadratic geometric coupling, and a
combined linear + quadratic (drag) damping.  The right-hand side of the
velocity ODE is, to machine precision:

    dv/dt = -x - 0.5*x**3 - z - 2*x*v**2 - 0.1*v - 0.1*v*|v|

Every coefficient was recovered exactly from the training data
(residual ~1e-15).  The relation is an explicit, pointwise function of
the observed state variables (x, v, z); the columns `t` and `e` are not
needed (`e` is a derived accumulated-work variable, e = integral of z*v).
"""


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    x = row["x"]
    v = row["v"]
    z = row["z"]

    dv_dt = (
        -x
        - 0.5 * x**3
        - z
        - 2.0 * x * v**2
        - 0.1 * v
        - 0.1 * v * abs(v)
    )

    return [{"dv_dt": dv_dt}]
