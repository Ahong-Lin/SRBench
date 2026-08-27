import math

# Discovered law: damped circadian oscillator (period ~24) whose fundamental
# amplitude is set by the previous light intensity via a Hill/sigmoid function,
# plus 2nd and 3rd harmonics (nonlinear limit-cycle shape).
#
#   A(I) = a + s * I^n / (K^n + I^n)
#   X(t,I) = exp(-g t) * [ A(I) sin(w t) + B cos(w t)
#                          + C2 sin(2 w t) + D2 cos(2 w t)
#                          + C3 sin(3 w t) + D3 cos(3 w t) ]

_a, _s, _K, _n = 0.99907, 0.98853, 0.80970, 4.90284
_g, _w = 0.00494, 0.26234
_B = -0.03440
_C2, _D2 = 0.07231, -0.36244
_C3, _D3 = -0.06309, 0.00744


def _predict(t: float, I: float) -> float:
    A = _a + _s * (I ** _n) / (_K ** _n + I ** _n)
    e = math.exp(-_g * t)
    return e * (
        A * math.sin(_w * t)
        + _B * math.cos(_w * t)
        + _C2 * math.sin(2 * _w * t)
        + _D2 * math.cos(2 * _w * t)
        + _C3 * math.sin(3 * _w * t)
        + _D3 * math.cos(3 * _w * t)
    )


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Predict X from t and I_light_prev using the discovered damped-oscillator law."""
    out = []
    for row in input_data:
        t = float(row["t"])
        I = float(row["I_light_prev"])
        out.append({"X": _predict(t, I)})
    return out
