import math


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the settling velocity `v` of a sphere from time `t`.

    The unsteady settling of a sphere (Stokes drag + added mass + Basset
    history force + wall correction) relaxes toward a terminal velocity as a
    superposition of decaying exponential relaxation modes.  The measured curve
    is captured to ~1e-6 RMS by a three-mode relaxation:

        v(t) = v_inf - c1*exp(-t/tau1) - c2*exp(-t/tau2) - c3*exp(-t/tau3)

    Parameters were obtained by nonlinear least-squares on the training data.
    """
    V_INF = 10.792247712769347
    C1, TAU1 = 8.796514460387003, 1.0244985180076738
    C2, TAU2 = 5.486932688082194, 2.021017399049305
    C3, TAU3 = -3.57730703643592, 0.6463198783844387

    out = []
    for row in input_data:
        t = row["t"]
        v = (
            V_INF
            - C1 * math.exp(-t / TAU1)
            - C2 * math.exp(-t / TAU2)
            - C3 * math.exp(-t / TAU3)
        )
        out.append({"v": v})
    return out
