"""Discovered law for the instantaneous acceleration dv_dt of a braking cart.

Model (interpretable, pointwise):

    dv_dt = -gamma * v  +  v**2 * g(x)

where x = cart_position and

    g(x) = sum_{n=1..3} [ a_n * sin(n*K*x) + b_n * cos(n*K*x) ]

Physical reading:
  * -gamma * v  : linear (viscous / rolling) resistance. The deceleration
                  vanishes as v -> 0, so there is no constant term.
  * v**2 * g(x) : quadratic (aerodynamic-type) drag whose coefficient varies
                  periodically along the track (a "washboard" road of spatial
                  wavelength L = 2*pi/K ~= 118). The periodic profile is not a
                  pure sinusoid, hence the first three spatial harmonics.

The brake_temperature and explicit time t carry no independent information for
dv_dt beyond what v and cart_position already provide (they are collinear with
them along the trajectory), so they do not appear in the law.

Parameters were fit by linear least squares on the full training trajectory;
the spatial frequency K was selected to be robust under forward (right-hand
time) extrapolation.
"""

import math

# Spatial frequency of the track modulation (rad per unit position).
K = 0.05329

# Linear-damping coefficient (coefficient multiplying v).
C0 = -0.060512018949799316

# Harmonic coefficients (a_n, b_n) for n = 1, 2, 3, multiplying v**2.
HARMONICS = (
    (0.0008172935432564376, -0.0003448665383063153),   # n = 1
    (-0.001214654029542435,  8.102287052493523e-05),   # n = 2
    (-0.00017842514397548078, -9.55668891294888e-05),  # n = 3
)


def _predict(v: float, x: float) -> float:
    osc = 0.0
    for n, (a, b) in enumerate(HARMONICS, start=1):
        phase = n * K * x
        osc += a * math.sin(phase) + b * math.cos(phase)
    return C0 * v + v * v * osc


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to a predicted dv_dt."""
    out = []
    for row in input_data:
        v = float(row["v"])
        x = float(row["cart_position"])
        out.append({"dv_dt": _predict(v, x)})
    return out
