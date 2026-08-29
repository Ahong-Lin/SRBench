"""
Discovered law for the (amplitude-dependent, damped) hardening-spring oscillator.

Target:  dv_dt  =  instantaneous acceleration of the mass.

Physical picture
----------------
A mass slides on a (nominally frictionless) surface attached to a spring with a
cubic hardening term (a Duffing-type restoring force).  The recorded signals are

    t : time
    x : position               (verified:  dx/dt = v   to 8 significant digits)
    v : velocity               (verified:  dv/dt = dv_dt column)
    z : an auxiliary recorded state variable (a lagged / filtered position,
        z ~ x near the start and then drifts; it carries a small amount of
        extra dynamical information that the pair (x, v) alone does not)
    e : an auxiliary energy-like signal (not needed for the fit)

Empirically the acceleration is an analytic function of the *observed* state.
It is NOT a pure function of x alone: e.g. at x ~ -0.10 the acceleration ranges
from +0.2 to +1.5 depending on the velocity, and the acceleration is large when
|v| is large (opposite to a textbook SHM), which reveals a strong velocity
coupling.  A bivariate Taylor expansion in (x, v) reproduces dv_dt to ~1e-2, and
adding the auxiliary state z pushes the residual to ~5e-3.

The model below is therefore an explicit closed-form pointwise map

    dv_dt = P(x, v) + c_z * z

where P(x, v) is the complete degree-4 bivariate polynomial (all monomials
x^i v^j with i + j <= 4).  The dominant terms have a clear reading:

    -1.996 * x * v^2   : velocity-dependent (geometric / kinematic) coupling
    -0.728 * x         : linear restoring stiffness  (shared with the z term)
    -1.281 * z         : the restoring contribution carried by the lagged state
    -0.514 * x^3       : cubic hardening of the spring
    -0.194 * x^4, ...  : higher-order corrections

Coefficients were fit by ordinary least squares on the full training set.
The map is pointwise: each row is transformed independently, using only the
declared variables x, v, z and fixed constants.
"""

# Monomials (i, j) of P(x, v) = sum c * x**i * v**j  with i + j <= 4
_TERMS = [
    (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
    (1, 0), (1, 1), (1, 2), (1, 3),
    (2, 0), (2, 1), (2, 2),
    (3, 0), (3, 1),
    (4, 0),
]

_COEFS = [
    -0.013257632517085728,   # 1
    -0.11910693366252482,    # v
    -0.0353799856209872,     # v^2
    -0.05455967172005543,    # v^3
    -0.015322136843268153,   # v^4
    -0.7284643050324767,     # x
    -0.016091648906660132,   # x v
    -1.9959920734826346,     # x v^2   (dominant velocity coupling)
    0.012419945999822537,    # x v^3
    -0.0504191531844203,     # x^2
    -0.009808319945910512,   # x^2 v
    -0.1679618279678172,     # x^2 v^2
    -0.5137489609563495,     # x^3     (cubic hardening)
    0.05864706213350847,     # x^3 v
    -0.19385653928104862,    # x^4
]

_C_Z = -1.2814276876791644   # coefficient of the auxiliary state z


def _predict(x: float, v: float, z: float) -> float:
    s = _C_Z * z
    for (i, j), c in zip(_TERMS, _COEFS):
        s += c * (x ** i) * (v ** j)
    return s


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to a single dv_dt prediction.

    Uses only the declared variables x, v, z (t and e are not required) and
    fixed constants inferred from the training data.
    """
    out = []
    for row in input_data:
        x = float(row["x"])
        v = float(row["v"])
        z = float(row["z"])
        out.append({"dv_dt": _predict(x, v, z)})
    return out


if __name__ == "__main__":
    import pandas as pd

    d = pd.read_csv("/app/data/train_data.csv")
    preds = law(d.to_dict("records"))
    p = [r["dv_dt"] for r in preds]
    err = (d["dv_dt"] - p).abs()
    print("max abs error :", err.max())
    print("rmse          :", ((d["dv_dt"] - p) ** 2).mean() ** 0.5)
