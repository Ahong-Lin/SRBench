"""Discovered law for predicting X from (t, I_light_prev).

Model
-----
X is the response of a lightly-damped oscillatory system whose amplitude is
modulated linearly by the light input.  It decomposes into:

    * a constant equilibrium term  D
    * a slowly relaxing (decaying) offset      A_dc * exp(-g0 t)
    * a damped ~24.5-unit oscillation           exp(-g1 t) * (c1 cos w1 t + s1 sin w1 t)
    * a persistent ~5.07-unit oscillation        exp(-g2 t) * (c2 cos w2 t + s2 sin w2 t)
    * a persistent ~12.15-unit oscillation       exp(-g3 t) * (c3 cos w3 t + s3 sin w3 t)

Every oscillatory / transient term is scaled by the light-coupling factor
(1 + k * I_light_prev); the equilibrium term D is not.

    X(t, I) = D + (1 + k*I) * [ A_dc*exp(-g0 t)
                                + exp(-g1 t)*(c1 cos w1 t + s1 sin w1 t)
                                + exp(-g2 t)*(c2 cos w2 t + s2 sin w2 t)
                                + exp(-g3 t)*(c3 cos w3 t + s3 sin w3 t) ]

All constants below were fitted on the training data.
"""

import math

# Light-coupling coefficient
K = 0.08655322894571076

# Damping rates (1/time-constant) for each mode
G0 = 0.008525838507231927   # slow relaxing offset  (tau ~117)
G1 = 0.03274708288782696    # damped oscillation     (tau ~30.5)
G2 = 5.1578776717433426e-05 # essentially undamped   (tau ~19000)
G3 = 0.0013460522750547929  # nearly undamped        (tau ~743)

# Angular frequencies
W1 = 0.25655899558908624    # period ~24.49
W2 = 1.2403366763308954     # period ~5.07
W3 = 0.5169836045368181     # period ~12.15

# Amplitudes
D = -0.041167067264055175   # equilibrium (uncoupled)
A_DC = 0.18731849326202324  # slow offset amplitude
C1, S1 = 1.434986111726976, 1.3570917440353067
C2, S2 = -0.21500720979277732, -0.10384976401453744
C3, S3 = 0.11793691103380498, 0.10064469802535833


def _predict(t: float, I: float) -> float:
    osc = (
        A_DC * math.exp(-G0 * t)
        + math.exp(-G1 * t) * (C1 * math.cos(W1 * t) + S1 * math.sin(W1 * t))
        + math.exp(-G2 * t) * (C2 * math.cos(W2 * t) + S2 * math.sin(W2 * t))
        + math.exp(-G3 * t) * (C3 * math.cos(W3 * t) + S3 * math.sin(W3 * t))
    )
    return D + (1.0 + K * I) * osc


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        t = float(row["t"])
        I = float(row["I_light_prev"])
        out.append({"X": _predict(t, I)})
    return out
