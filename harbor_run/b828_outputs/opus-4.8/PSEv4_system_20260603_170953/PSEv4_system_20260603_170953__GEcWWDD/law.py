import math


# Damped, driven Duffing oscillator discovered from the training data:
#   dv/dt = -delta*v - alpha*x - beta*x**3 + gamma*sin(omega*t)
# Parameters fitted by nonlinear least squares (R^2 = 0.9986).
ALPHA = 0.52976335   # linear restoring stiffness
BETA = 0.84983161    # cubic (nonlinear) stiffness
DELTA = 0.20856835   # linear damping coefficient
GAMMA = 1.16907668   # forcing amplitude
OMEGA = 0.9990129    # forcing angular frequency


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        t = row["t"]
        x = row["x"]
        v = row["v"]
        dv_dt = (
            -DELTA * v
            - ALPHA * x
            - BETA * x ** 3
            + GAMMA * math.sin(OMEGA * t)
        )
        out.append({"dv_dt": dv_dt})
    return out
