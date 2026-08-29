"""Discovered pointwise law for X = f(t, I_light_prev).

The data behave like a light-driven, damped circadian oscillator that relaxes
from a large-amplitude transient toward a low-amplitude steady rhythm.  X is an
explicit closed-form function of the two declared inputs:

    X(t, I) = off
            + D1 * exp(-gd * t)                                  # slow mean relaxation
            + exp(-g1 * t)  * (a1  * cos(w1  t) + b1  * sin(w1  t))   # circadian ~24.6 (transient A)
            + exp(-g1b* t)  * (a1b * cos(w1b t) + b1b * sin(w1b t))   # circadian ~23.5 (transient B, shapes envelope)
            + exp(-gh * t)  * (h1  * cos(wh  t) + h2  * sin(wh  t))   # ~12 h harmonic (nearly persistent)
            + (a2 * cos(w2 t) + b2 * sin(w2 t))                       # persistent ultradian ~5.07
            + I * exp(-g3 * t) * (c1 * cos(w1 t) + c2 * sin(w1 t))    # light coupling (decaying)

with w = 2*pi / T for each period T.  All constants were fitted on the training
set (train RMSE ~0.008, max abs error ~0.05; the data are essentially noise-free).
"""

import math

# --- fitted constants ---
OFF  = -0.027722942493387345
D1   =  0.21223164852528761
GD   =  0.010911104538534656

A1   =  1.7382735940564789
B1   =  1.4964405935605005
G1   =  0.036353012358963
T1   = 24.57338722298146

A1B  = -0.41359384690116824
B1B  = -0.27104559815084045
G1B  =  0.09441191022678436
T1B  = 23.51906745855742

H1   =  0.13166063447384016
H2   =  0.1197562818156416
GH   =  0.0018801723040084075
TH   = 12.146350786491864

A2   = -0.23375701512973435
B2   = -0.11148994080409506
T2   =  5.065922014938385

C1   =  0.16680756244144943
C2   =  0.1488232810607039
G3   =  0.034920928370049925

_2PI = 2.0 * math.pi
W1   = _2PI / T1
W1B  = _2PI / T1B
WH   = _2PI / TH
W2   = _2PI / T2


def _predict(t: float, I: float) -> float:
    x = OFF
    x += D1 * math.exp(-GD * t)
    x += math.exp(-G1 * t) * (A1 * math.cos(W1 * t) + B1 * math.sin(W1 * t))
    x += math.exp(-G1B * t) * (A1B * math.cos(W1B * t) + B1B * math.sin(W1B * t))
    x += math.exp(-GH * t) * (H1 * math.cos(WH * t) + H2 * math.sin(WH * t))
    x += A2 * math.cos(W2 * t) + B2 * math.sin(W2 * t)
    x += I * math.exp(-G3 * t) * (C1 * math.cos(W1 * t) + C2 * math.sin(W1 * t))
    return x


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to a predicted X.

    Each row must contain 't' and 'I_light_prev'.  Returns a list with one
    {'X': value} dict per input row (the verifier calls with a single row).
    """
    out = []
    for row in input_data:
        t = float(row["t"])
        I = float(row["I_light_prev"])
        out.append({"X": _predict(t, I)})
    return out
