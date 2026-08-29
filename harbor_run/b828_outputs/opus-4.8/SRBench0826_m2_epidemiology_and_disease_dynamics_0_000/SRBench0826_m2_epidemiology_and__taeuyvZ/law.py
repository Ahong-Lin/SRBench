"""
Discovered law for dI/dt in a saturating-incidence epidemic model.

Empirical finding (see explain.md for the full derivation):

  * The susceptible depletion obeys, to machine precision,
        dS/dt = -0.5 * S * I / (N + I)          with N = S + E + I + R = 1000
    i.e. a SATURATING (Holling type-II) incidence rather than the classical
    bilinear beta*S*I/N.  The effective transmission rate falls from 0.4995
    at I->0 down to ~0.468 at the epidemic peak, and 1/beta_eff is exactly
    linear in I: 1/beta_eff = 2 + 2 I/N  ==>  incidence = 0.5 S I /(N+I).

  * dI/dt is, to R^2 = 0.99974, a pointwise function of S and I ONLY.
    Adding E or R as predictors does not reduce the residual: the exposed
    class E lags I (E peaks AFTER I), so E is downstream of I and does not
    enter the I balance.  The infectious balance is well described by an
    infection inflow with the same saturating structure minus a linear
    removal term:

        dI/dt = c1 * S*I/(N+I)  +  c2 * I  +  c3 * S*I^2/((N+I)*N)

    which can also be written as
        dI/dt = S*I/(N+I) * (c1 + c3 * I/N) + c2 * I .

Coefficients fitted on the training trajectory:
    c1 =  0.44102556
    c2 = -0.19678775
    c3 = -1.81822299
"""

C1 = 0.44102556
C2 = -0.19678775
C3 = -1.81822299


def law(input_data):
    """Map each input row independently to a dI_dt prediction.

    Parameters
    ----------
    input_data : list[dict[str, float]]
        Each dict has keys t, S, E, I, R.

    Returns
    -------
    list[dict[str, float]]
        One dict {"dI_dt": value} per input row.
    """
    out = []
    for row in input_data:
        S = row["S"]
        E = row["E"]
        I = row["I"]
        R = row["R"]

        # Total (conserved) population; equals 1000 in this experiment.
        N = S + E + I + R
        D = N + I  # saturating-incidence denominator

        # Guard against a degenerate empty population.
        if D <= 0.0 or N <= 0.0:
            out.append({"dI_dt": 0.0})
            continue

        sat = S * I / D                    # saturating incidence shape
        dI_dt = C1 * sat + C2 * I + C3 * sat * (I / N)

        out.append({"dI_dt": dI_dt})
    return out


if __name__ == "__main__":
    # quick self-check against a couple of hand values
    demo = [
        {"t": 0.0, "S": 999.0, "E": 0.0, "I": 1.0, "R": 0.0},
        {"t": 108.0, "S": 299.765081, "E": 0.510101, "I": 0.913525, "R": 698.811293},
    ]
    print(law(demo))
