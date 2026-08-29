import math


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts X from t and I_light_prev using a discovered damped, light-driven
    circadian-oscillator law:

        X = exp(-t/tau) * [ (a + b*I) * sin(w*t) + c*cos(w*t) ]
            + d*cos(2*w*t) + e*sin(2*w*t) + g*sin(3*w*t) + f

    The fundamental oscillation (period ~24) has an amplitude that grows linearly
    with the previous light intensity I_light_prev and slowly decays in time.
    The 2nd/3rd harmonics capture the non-sinusoidal waveform shape.
    """
    # Parameters fitted to the training data (R^2 ~ 0.994)
    w = 0.26222615177484626      # angular frequency (period = 2*pi/w ~ 23.96)
    a = 0.9288061797405479       # base fundamental amplitude
    b = 0.6664768452063199       # light-intensity gain on amplitude
    c = -0.03382890199724697     # fundamental cosine (phase) term
    tau = 182.4724933359289      # amplitude decay time constant
    d = -0.3010618838576971      # cos(2w t) amplitude
    e = 0.060653938771361736     # sin(2w t) amplitude
    g = -0.048471312644302565    # sin(3w t) amplitude
    f = -0.006306957192730583    # constant offset

    results = []
    for row in input_data:
        t = row["t"]
        I = row["I_light_prev"]
        env = math.exp(-t / tau)
        X = (
            env * ((a + b * I) * math.sin(w * t) + c * math.cos(w * t))
            + d * math.cos(2 * w * t)
            + e * math.sin(2 * w * t)
            + g * math.sin(3 * w * t)
            + f
        )
        results.append({"X": X})
    return results
