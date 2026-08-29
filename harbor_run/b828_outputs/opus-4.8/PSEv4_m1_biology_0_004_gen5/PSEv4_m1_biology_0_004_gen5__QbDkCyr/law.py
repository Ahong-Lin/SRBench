import math

# Discovered law: damped circadian oscillator (period ~24.6) relaxing to an
# equilibrium, plus a small transient response to the previous light input.
#
#   X(t, I) = exp(-t/TAU) * ( A_COS*cos(w t) + A_SIN*sin(w t) )
#             + B + M * exp(-t/TAU) * I_light_prev
#   with w = 2*pi / T
#
# Parameters fitted on the training data (least squares).

TAU = 30.291324552054245     # amplitude decay time constant
T = 24.602366535816387       # oscillation period
A_COS = 1.6232927513862343   # cosine quadrature amplitude
A_SIN = 1.4219051725183716   # sine quadrature amplitude
B = 0.052143170432897165     # equilibrium offset
M = 0.13026107179930513      # transient light-response gain

_W = 2.0 * math.pi / T


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    t = row["t"]
    I = row["I_light_prev"]

    env = math.exp(-t / TAU)
    osc = env * (A_COS * math.cos(_W * t) + A_SIN * math.sin(_W * t))
    x = osc + B + M * env * I
    return [{"X": x}]
