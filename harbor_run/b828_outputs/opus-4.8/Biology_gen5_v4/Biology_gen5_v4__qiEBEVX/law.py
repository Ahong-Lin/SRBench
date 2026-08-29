import math


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discovered law: a decaying, light-modulated circadian oscillator.

    X(t, I) = C + exp(-lam*t) * [ (A1 + B1*tanh(k*I)) * cos(w*t + p1)
                                  + C2 * cos(2*w*t + p2)
                                  + C3 * cos(3*w*t + p3) ]

    The fundamental circadian rhythm (period 2*pi/w ~ 24) has an amplitude that
    saturates with the previous light input I (tanh), while the 2nd and 3rd
    harmonics shape the (non-sinusoidal) waveform. The whole envelope decays
    slowly in time (exp(-lam*t)).
    """
    C = -0.00558472
    lam = 0.00496369
    w = 0.26235187
    k = 0.67710162
    A1 = 0.76977133
    B1 = 1.48678849
    p1 = -1.59340373
    C2 = -0.37115372
    p2 = 0.18832654
    C3 = 0.06289031
    p3 = 1.45318720

    out = []
    for row in input_data:
        t = row["t"]
        I = row["I_light_prev"]
        env = math.exp(-lam * t)
        val = C + env * (
            (A1 + B1 * math.tanh(k * I)) * math.cos(w * t + p1)
            + C2 * math.cos(2 * w * t + p2)
            + C3 * math.cos(3 * w * t + p3)
        )
        out.append({"X": val})
    return out
