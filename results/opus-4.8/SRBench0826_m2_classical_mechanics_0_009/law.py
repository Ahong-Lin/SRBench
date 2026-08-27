"""Discovered law for predicting dv_dt (acceleration) of an anharmonic oscillator.

The experiment is a mass on a hardening (cubic) spring -- a Duffing oscillator.
The true dynamical state is 2-dimensional: the reported `x` (a position-like
coordinate, with dx/dt = v exactly) and its velocity `v`.  The extra columns
`z` and `e` turn out to be smooth functions of (x, v):  z = g(x, v),
e = integral of v*z.  Because the reported `x` is a *nonlinear transform* of the
underlying Duffing position, the acceleration is NOT a function of x alone; it
picks up velocity-dependent terms (notably a strong x*v^2 Jacobian term).

Empirically dv_dt is captured to ~1e-3 RMSE by a cubic polynomial in (x, v, z).
This form was selected because it is the most robust temporal extrapolator
(it degrades gracefully on held-out future segments, unlike higher-degree or
e-including variants which overfit).  Coefficients were fit by least squares on
the full training set.
"""

# Monomials over (x, v, z) up to total degree 3, as index tuples into [x, v, z].
_COMBOS = [
    (), (0,), (1,), (2,),
    (0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2),
    (0, 0, 0), (0, 0, 1), (0, 0, 2), (0, 1, 1), (0, 1, 2),
    (0, 2, 2), (1, 1, 1), (1, 1, 2), (1, 2, 2), (2, 2, 2),
]

_COEFS = [
    -0.01280125006298789,   # 1
    -0.6519703636365499,    # x
    -0.09936547909690524,   # v
    -1.3586286159692909,    # z
    -0.34554146070663777,   # x*x
    -0.3594706619099069,    # x*v
    0.5969298750432455,     # x*z
    -0.08671615020404055,   # v*v
    0.3710506461329505,     # v*z
    -0.3592151626308075,    # z*z
    -0.48845724364643645,   # x*x*x
    0.35978546911548526,    # x*x*v
    -0.24855695324850557,   # x*x*z
    -1.961225312198185,     # x*v*v
    -0.43582652095999097,   # x*v*z
    0.004487475468654687,   # x*z*z
    -0.0061859350428198415, # v*v*v
    -0.08130649622289086,   # v*v*z
    0.189575616667411,      # v*z*z
    0.12139675317461063,    # z*z*z
]


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    out = []
    for row in input_data:
        vars_ = (row["x"], row["v"], row["z"])
        val = 0.0
        for combo, coef in zip(_COMBOS, _COEFS):
            term = coef
            for idx in combo:
                term *= vars_[idx]
            val += term
        out.append({"dv_dt": val})
    return out
