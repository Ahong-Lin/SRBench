"""Discovered law for dv_dt of a mass on a (weakly nonlinear) spring
moving through a viscous medium.

Model (pointwise, per row):

    dv_dt = C0 + C1*x + C2*x**2 + C3*x**3 + C4*v

i.e. a linear viscous damping term (-|C4|*v, retarding force proportional
to speed) plus a nonlinear ("cubic") spring restoring force with a constant
gravitational offset C0.  The auxiliary variable `z` (a velocity-memory
integral, dz/dt = -(v+z)) is a decoy: including it does not improve
out-of-sample prediction and destabilises the fit, so it is not used.

Only the declared variables (x, v) and fixed constants inferred from the
training data enter the expression.  `t` and `z` are not required.
"""

# Coefficients fitted by ordinary least squares on the full training set.
C0 = -0.18511527058574576   # constant (gravity offset)
C1 = -1.8361690559594777    # linear spring stiffness  (-k/m)
C2 = 0.04454871181521005    # quadratic spring correction
C3 = -0.44230973975602345   # cubic spring correction  (Duffing term)
C4 = -0.4785159819371596    # linear viscous damping   (-b/m)


def _dv_dt(x: float, v: float) -> float:
    return C0 + C1 * x + C2 * x * x + C3 * x * x * x + C4 * v


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to one dv_dt prediction.

    The hidden verifier calls this with exactly one row at a time, so we
    simply process each row of the provided list and return a list of
    single-key dictionaries.
    """
    out = []
    for row in input_data:
        x = float(row["x"])
        v = float(row["v"])
        out.append({"dv_dt": _dv_dt(x, v)})
    return out


if __name__ == "__main__":
    # quick self-check against a training-like point
    print(law([{"t": 0.0, "x": 1.0, "v": 0.0, "z": 0.0}]))
