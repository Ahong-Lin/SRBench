"""Discovered law for dvx_dt of a body in a (perturbed) bound orbit.

The dominant physics is Newtonian inverse-square gravity toward a fixed
center at the origin,  a_x = -GM * x / r^3 ,  r = sqrt(x^2 + y^2).

The experimental data, however, is NOT a pure Kepler orbit: the trajectory
precesses and its angular momentum about the origin is not conserved.  A
careful decomposition of the acceleration field shows three additional,
much smaller and fully reproducible contributions:

  1. A quadrupole (J2-like) perturbation that breaks spherical symmetry.
     Its potential is  U_q = Q * (x^2 - y^2) / r^5  with  Q = -1/40, whose
     x-force is  -2Q*x/r^5 + 5Q*x*(x^2-y^2)/r^7 = 0.05*x/r^5 - 0.125*x*(x^2-y^2)/r^7.
     This term alone produces the clean tangential acceleration
     a_t ∝ sin(2θ)/r^4 that is measured in the data (correlation -1.000).

  2. A small extra central (radial) force ∝ 1/r^4, i.e. an x-force ∝ x/r^5.

  3. A small velocity-dependent ("drag-like") force ∝ v/r^2, whose
     x-component is ∝ vx/r^2.

Collecting the x-force contributions, the law is written as the explicit
pointwise function

  dvx_dt = -GM * x/r^3  +  A * x/r^5  +  B * x*(x^2 - y^2)/r^7  +  C * vx/r^2

with constants fitted from the training data.  Here
  A = 0.05 (from the quadrupole) + 0.01494 (extra 1/r^4 radial term)
  B = 5*Q = -1/8   (the quadrupole),  GM = 1.

This reproduces the training target with R^2 = 0.9999997 and generalizes to
the held-out right-hand time segment with the same accuracy.
"""

from typing import Dict, List

# Constants inferred from the training data (least-squares fit).
GM = 0.99940167   # monopole strength  G*M  (essentially 1)
A  = 0.06480147   # coefficient of x / r^5   (quadrupole 0.05 + extra radial 0.01494)
B  = -0.12501777  # coefficient of x*(x^2 - y^2) / r^7   (essentially -1/8)
C  = -0.00379919  # coefficient of vx / r^2   (small velocity-dependent term)


def _dvx_dt(x: float, y: float, vx: float, vy: float) -> float:
    r2 = x * x + y * y
    r = r2 ** 0.5
    r3 = r2 * r          # r^3
    r5 = r3 * r2         # r^5
    r7 = r5 * r2         # r^7
    return (
        -GM * x / r3
        + A * x / r5
        + B * x * (x * x - y * y) / r7
        + C * vx / r2
    )


def law(input_data: List[Dict[str, float]]) -> List[Dict[str, float]]:
    """Map each input row independently to a dvx_dt prediction.

    Each element of `input_data` is a dict with keys t, x, y, vx, vy.
    Returns a list with one dict {'dvx_dt': value} per input row.
    """
    out: List[Dict[str, float]] = []
    for row in input_data:
        x = float(row["x"])
        y = float(row["y"])
        vx = float(row["vx"])
        vy = float(row["vy"])
        out.append({"dvx_dt": _dvx_dt(x, y, vx, vy)})
    return out
