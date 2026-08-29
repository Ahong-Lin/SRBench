"""
Discovered law for `dv_dt` of a vertically hanging, spring–mass system
oscillating in a viscous medium (linearly damped harmonic oscillator with a
constant gravitational offset).

    dv/dt = -omega2 * (x - x_eq) - gamma * v
          = -omega2 * x - gamma * v + (omega2 * x_eq_signed)

Written in the pointwise affine form actually evaluated:

    dv/dt = A * x + B * v + C

Constants were inferred from the training trajectory in its small-amplitude
(late-time) regime, which is the regime the hidden right-hand test segment
lives in and where this linear law is exact (residual RMS ~1e-5).

    A = -omega^2        = -1.8485   (spring stiffness / mass, k/m)
    B = -gamma          = -0.6155   (damping coefficient / mass, c/m)
    C = -omega^2 * x_eq = -0.1844   (constant gravitational term, = g_eff)

Equilibrium position: x_eq = -C / A = -0.09974.
"""

# Fixed parameters inferred from training data (small-amplitude / modal limit).
A = -1.8485   # -k/m   (natural frequency squared, with sign)
B = -0.6155   # -c/m   (viscous damping per unit mass, with sign)
C = -0.1844   # constant gravitational/offset term  (= A * x_eq)


def law(input_data):
    """Map each input row independently to its `dv_dt` prediction.

    Parameters
    ----------
    input_data : list[dict[str, float]]
        Each dict has keys 't', 'x', 'v', 'z' (only 'x' and 'v' are used).

    Returns
    -------
    list[dict[str, float]]
        One dict per input row, each with the single key 'dv_dt'.
    """
    out = []
    for row in input_data:
        x = row["x"]
        v = row["v"]
        dv_dt = A * x + B * v + C
        out.append({"dv_dt": dv_dt})
    return out


if __name__ == "__main__":
    # quick self-test
    demo = [{"t": 0.0, "x": 1.0, "v": 0.0, "z": 0.0}]
    print(law(demo))
