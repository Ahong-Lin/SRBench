"""Discovered acceleration law for the observed dynamical system.

dv_dt = a1*x + a3*x^3 + b1*v + b3*v^3 + c*Fh + d*Fh2

A Duffing-type oscillator: a near-unit linear restoring term (-x) with a
hardening cubic correction, weak linear + cubic velocity damping, and two
external forcing channels (Fh, Fh2). Parameters fitted by least squares on the
training data; validated to extrapolate to the held-out later time segment.
"""

# Fitted coefficients (no intercept; the constant term is ~1e-4, negligible).
A1 = -0.9976296164248579   # x
A3 = -0.05328716357635006  # x^3
B1 = -0.027546839082800343 # v
B3 = -0.013426082453657952 # v^3
C  = -0.10312242345924784  # Fh
D  = -0.05105020234999799  # Fh2


def _dv_dt(x: float, v: float, Fh: float, Fh2: float) -> float:
    return A1 * x + A3 * x**3 + B1 * v + B3 * v**3 + C * Fh + D * Fh2


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        x = row["x"]
        v = row["v"]
        Fh = row["Fh"]
        Fh2 = row["Fh2"]
        out.append({"dv_dt": _dv_dt(x, v, Fh, Fh2)})
    return out
