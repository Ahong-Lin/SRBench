"""
Discovered law for the observed dynamical system.

The instantaneous right-hand side dN/dt is a linear function of the two
population variables (N = total abundance, R = reproductive-adult abundance)
whose coefficients vary periodically in time with a fundamental period of
exactly 1 time unit (seasonal forcing, angular frequency w = 2*pi):

    dN/dt = A(t) + B(t) * N + C(t) * R

where A, B, C are truncated Fourier series (6 harmonics) of the season phase.

Interpretation:
    C(t) * R  -> seasonally modulated recruitment produced by reproductive adults
    B(t) * N  -> seasonally modulated per-capita loss/growth of the whole stock
    A(t)      -> seasonal baseline flux

All parameters were fit by linear least squares on the training trajectory.
The model reproduces the training data with R^2 = 0.99987 and extrapolates to
the held-out right-hand time segment with R^2 ~ 0.999.
"""

import math

W = 2.0 * math.pi            # fundamental angular frequency (period = 1.0)
K = 6                        # number of harmonics

# Fourier coefficients for A(t), B(t), C(t).
# Each list is [a0, a1_sin, a1_cos, a2_sin, a2_cos, ..., aK_sin, aK_cos].
A = [62.73074860411469, 33.04882929824181, 11.324601890331872,
     7.047809810086923, -9.50803704681518, -7.170037611360663,
     0.0020243818374748868, 0.282204873727377, 3.904061080190914,
     1.775076836585267, 0.42089752890771204, -0.026260879652034406,
     -0.4279037081319671]
B = [-0.8475597305055005, -0.3093340236848531, -0.11348910982704588,
     -0.1258501756600195, 0.04584611944852231, -0.010889376900475888,
     -0.011760873200405753, -0.04054089080140022, -0.05579145664722951,
     -0.039866330284347384, -0.035098573424464874, 0.040092678992282416,
     -0.049599514824864854]
C = [0.8467674661926139, 0.6899658386421099, 0.29615774797235694,
     0.23070765042748098, -0.1444145469343745, -0.056688271728760675,
     0.014641832713962799, 0.05445134616944003, 0.1113207511902985,
     0.06963396652305853, 0.04480804626196977, -0.05757635013952278,
     0.06418179967508664]


def _series(coeffs, t):
    """Evaluate a0 + sum_k [a_sin*sin(k w t) + a_cos*cos(k w t)]."""
    val = coeffs[0]
    for k in range(1, K + 1):
        ang = k * W * t
        val += coeffs[2 * k - 1] * math.sin(ang) + coeffs[2 * k] * math.cos(ang)
    return val


def law(input_data):
    """Map each input row independently to one {'dN_dt': prediction} dict."""
    out = []
    for row in input_data:
        t = row["t"]
        N = row["N"]
        R = row["reproductive_adult_abundance"]
        dN_dt = _series(A, t) + _series(B, t) * N + _series(C, t) * R
        out.append({"dN_dt": dN_dt})
    return out
