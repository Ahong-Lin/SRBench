"""Discovered law for dvx_dt.

Physical model (see explain.md for the full derivation):

    A small body orbits a central body whose gravity is Newtonian at leading
    order but carries an l=2 (quadrupole) moment, plus a weak drag that removes
    energy slowly.  Writing r = sqrt(x^2 + y^2), the x-acceleration is

        dvx_dt = -GM * x/r^3                      # Newtonian monopole
                 + a2 * x/r^5                     # axisymmetric part of quadrupole
                 + a3 * x*(x^2 - y^2)/r^7         # cos(2 theta) part of quadrupole
                 - k  * vx/r^2                    # weak drag ~ v / r^2

    The quadrupole terms are the Cartesian gradient of a potential
        U_quad = (C + B*cos 2theta)/r^3 = C/r^3 + B*(x^2 - y^2)/r^5 ,
    which produces the observed tangential force  a_t ~ sin(2 theta)/r^4  and the
    retrograde apsidal precession.  The drag term (proportional to v/r^2, strongest
    near perihelion) accounts for the slow decay of the perihelion distance and the
    non-conservation of energy/angular momentum.

    All coefficients are fixed constants fit once to the training data.
"""

# Constants inferred from the training data (least squares on the exact target).
GM_X = -0.9994016665754775   # coefficient of  x/r^3      (= -GM,        GM ~= 1.0)
A2   =  0.06480146816678291  # coefficient of  x/r^5      (= 3C - 2B)
A3   = -0.1250177660082093   # coefficient of  x*(x^2-y^2)/r^7   (= 5B,  B ~= -0.025)
KDRG = -0.003799193346860818 # coefficient of  vx/r^2     (= -k,         k ~= 0.0038)


def _dvx_dt(x: float, y: float, vx: float) -> float:
    r2 = x * x + y * y
    r = r2 ** 0.5
    inv_r3 = 1.0 / (r2 * r)          # 1/r^3
    inv_r5 = inv_r3 / r2             # 1/r^5
    inv_r7 = inv_r5 / r2             # 1/r^7
    return (GM_X * x * inv_r3
            + A2 * x * inv_r5
            + A3 * x * (x * x - y * y) * inv_r7
            + KDRG * vx / r2)


def law(input_data):
    """Map each input row independently to a dvx_dt prediction.

    input_data: list of dicts with keys t, x, y, vx, vy (each mapped independently).
    Returns a list of dicts, each with key 'dvx_dt'.
    """
    out = []
    for row in input_data:
        x = float(row["x"])
        y = float(row["y"])
        vx = float(row["vx"])
        out.append({"dvx_dt": _dvx_dt(x, y, vx)})
    return out
