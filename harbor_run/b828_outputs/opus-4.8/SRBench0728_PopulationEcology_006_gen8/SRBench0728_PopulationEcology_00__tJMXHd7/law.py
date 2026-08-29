import math

# Seasonally-forced bilinear population model (period P = 1.0):
#   dN/dt = b(t)*R + c(t)*N*R + a(t)*N
# where b(t), c(t), a(t) are periodic (period 1) seasonal coefficient
# functions represented as 6-harmonic Fourier series in phase 2*pi*t.
# b(t): per-adult seasonal recruitment; a(t): seasonal per-capita loss;
# c(t): seasonal density-dependent (adult x total) interaction.

W = 2.0 * math.pi
NH = 6

# Fourier coefficients [const, sin1, cos1, sin2, cos2, ...] fitted on the
# full training set (extrapolation R^2 ~ 0.9999 on held-out late segment).
_C_R = [1.7694885353198617, 0.9234255973211231, 0.3988873801132972,
        0.20081266725036767, -0.29369901547293564, -0.2208185860143364,
        -0.02361430085511771, 0.03205168697300608, 0.10342753561272434,
        0.09070718686581296, -0.0001229615068689266, -0.037381809768299606,
        0.045990216988776145]
_C_RN = [-0.0029414420707795496, -0.0014269518742462892, -0.0006847251753842043,
         -0.0003268262721514703, 0.00040361277891839964, 0.00034426662453196366,
         1.5330741295338512e-05, 3.94156193414541e-06, -0.0001723521108363546,
         -8.855916951540713e-05, -1.3599301035838174e-05, -1.913949767784473e-06,
         2.607269648574606e-05]
_C_N = [-0.7634956616423254, -0.09590978249809484, -0.041431805396897656,
        -0.024656413837577967, 0.04244213006935221, 0.019294925789608564,
        0.015258380299881816, -0.022600335410295457, -0.005018776239981371,
        -0.03341910834867001, 0.0004989586536714719, 0.025558610336524772,
        -0.04236110958324437]


def _series(coef, t):
    val = coef[0]
    for h in range(1, NH + 1):
        val += coef[2 * h - 1] * math.sin(h * W * t)
        val += coef[2 * h] * math.cos(h * W * t)
    return val


def law(input_data):
    out = []
    for row in input_data:
        t = row["t"]
        N = row["N"]
        R = row["reproductive_adult_abundance"]
        b = _series(_C_R, t)
        c = _series(_C_RN, t)
        a = _series(_C_N, t)
        dN_dt = b * R + c * N * R + a * N
        out.append({"dN_dt": dN_dt})
    return out
