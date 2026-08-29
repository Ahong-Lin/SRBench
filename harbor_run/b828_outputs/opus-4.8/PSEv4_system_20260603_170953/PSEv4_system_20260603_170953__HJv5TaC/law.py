"""
Discovered acceleration law for a periodically driven nonlinear oscillator.

    dv/dt = R(x)  -  delta * sin(v)  +  gamma * sin(t)

where
  * R(x) is an odd, "hardening" restoring force (stiffening spring), well
    represented on the observed range |x| <~ 1.8 by the odd polynomial
        R(x) = a1*x + a3*x^3 + a5*x^5 + a7*x^7 + a9*x^9
  * -delta*sin(v) is a (nonlinear) velocity damping term,
  * +gamma*sin(t) is the external periodic drive (unit angular frequency).

All coefficients are fixed constants inferred from the training data.
The function maps each input row independently to one dv_dt prediction.
"""

# Restoring-force polynomial coefficients R(x) = a1 x + a3 x^3 + a5 x^5 + a7 x^7 + a9 x^9
A1 = -0.791971
A3 = -0.172366
A5 = -0.568575
A7 = 0.198037
A9 = -0.026032

# Nonlinear damping amplitude:  -DELTA * sin(v)
DELTA = 0.2994

# Periodic drive amplitude:  +GAMMA * sin(t)   (angular frequency = 1)
GAMMA = 1.197581


def _dv_dt(t: float, x: float, v: float) -> float:
    import math
    x2 = x * x
    # Horner form for the odd restoring polynomial
    restoring = x * (A1 + x2 * (A3 + x2 * (A5 + x2 * (A7 + x2 * A9))))
    damping = -DELTA * math.sin(v)
    drive = GAMMA * math.sin(t)
    return restoring + damping + drive


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Predict dv_dt for a single input row.

    The hidden verifier calls law([row]) with exactly one row at a time and
    expects a list containing exactly one dict with key 'dv_dt'.
    """
    out = []
    for row in input_data:
        t = float(row["t"])
        x = float(row["x"])
        v = float(row["v"])
        out.append({"dv_dt": _dv_dt(t, x, v)})
    return out
