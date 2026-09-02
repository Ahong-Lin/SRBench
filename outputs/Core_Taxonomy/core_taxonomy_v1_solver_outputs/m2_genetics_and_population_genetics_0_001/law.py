import math

# Discovered closed-form law for the decay of expected heterozygosity.
#
#   dH/dt = -k*(H - Heq)                    # relaxation toward a drift/mutation
#                                           #   equilibrium (dominant decay)
#           + H*(g1*sin(w t) + g2*cos(w t)) # periodic modulation of the decay
#                                           #   rate (fluctuating effective size)
#           + (a1*sin(w t) + a2*cos(w t))   # additive periodic forcing
#           + (b1*t*sin(w t)+b2*t*cos(w t)) # slow growth of the forcing amplitude
#           + (h1*sin(2w t)+h2*cos(2w t))   # 2nd harmonic of the forcing
#           + c1*t + c2*t**2                # slow secular drift of the baseline
#
# with a fixed angular frequency w = 2*pi/50 (period 50 generations).
#
# Equivalently written as a linear combination of fixed basis functions of the
# two declared variables (t, H); the coefficients below were fitted by ordinary
# least squares on the training trajectory (R^2 = 0.99990, max abs err 4.2e-5).

W = 2.0 * math.pi / 50.0

# Coefficients: [const, H, t, t^2, sin, cos, t*sin, t*cos, H*sin, H*cos, sin2, cos2]
C = [
    0.004386223834333981,
    -0.0269538631684663,
    4.305649253032357e-06,
    -4.271544035294487e-09,
    -4.608133615178393e-05,
    6.272684417949051e-05,
    -5.946847256186306e-07,
    -2.8902383525405524e-08,
    0.00400256087427458,
    -0.000522396866632811,
    5.681144335716708e-06,
    6.60911255604e-05,
]


def _predict(t: float, H: float) -> float:
    s, c = math.sin(W * t), math.cos(W * t)
    s2, c2 = math.sin(2.0 * W * t), math.cos(2.0 * W * t)
    feats = [1.0, H, t, t * t, s, c, t * s, t * c, H * s, H * c, s2, c2]
    return sum(coef * f for coef, f in zip(C, feats))


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    t = float(row["t"])
    H = float(row["H"])
    return [{"dH_dt": _predict(t, H)}]
