"""
Discovered law for dvx_dt of a small body orbiting a heavy central body.

The dynamics are NOT a pure Kepler inverse-square field.  The acceleration is a
static, position-only, conservative field derived from the potential

        Phi(x, y) = -GM/r  +  A/r^3  +  B*(x^2 - y^2)/r^5            (r = sqrt(x^2+y^2))

i.e. a monopole (Newtonian gravity) plus a small axisymmetric 1/r^3 correction
(A term) plus a fixed quadrupole aligned with the x-axis (B term, = B*cos(2*theta)/r^3).

The x-acceleration is  dvx_dt = -dPhi/dx :

    dvx_dt = -GM*x/r^3  +  3*A*x/r^5  -  B*(2*x/r^5 - 5*(x^2 - y^2)*x/r^7)

Fitted constants (from the training trajectory):
    GM = 0.9936862677229467
    A  = 0.004362365100161962
    B  = -0.02494062746642001

Fit quality on the training set: R^2 = 0.99998, RMS residual ~= 0.0098.
The relation is a pointwise function of the observed positions (x, y) only.
"""

GM = 0.9936862677229467
A = 0.004362365100161962
B = -0.02494062746642001


def _dvx_dt(x: float, y: float) -> float:
    r2 = x * x + y * y
    r = r2 ** 0.5
    inv_r3 = 1.0 / (r2 * r)      # 1/r^3
    inv_r5 = inv_r3 / r2         # 1/r^5
    inv_r7 = inv_r5 / r2         # 1/r^7
    # -dPhi/dx
    monopole = -GM * x * inv_r3
    iso_corr = 3.0 * A * x * inv_r5
    quad = -B * (2.0 * x * inv_r5 - 5.0 * (x * x - y * y) * x * inv_r7)
    return monopole + iso_corr + quad


def law(input_data):
    """Map each input row independently to a dvx_dt prediction.

    Parameters
    ----------
    input_data : list[dict[str, float]]
        Each dict has keys t, x, y, vx, vy.  Only x and y are used.

    Returns
    -------
    list[dict[str, float]]
        One dict per input row with key 'dvx_dt'.
    """
    out = []
    for row in input_data:
        x = row["x"]
        y = row["y"]
        out.append({"dvx_dt": _dvx_dt(x, y)})
    return out
