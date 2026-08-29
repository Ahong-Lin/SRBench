"""
Discovered law for dI_dt in a SEIR-like epidemic with saturating incidence.

The law is a pure, pointwise function of the state (t, S, E, I, R). It carries
no state between calls, reads no files, does no interpolation / differentiation,
and does not depend on the ordering of the input rows. Each input row is mapped
independently to exactly one prediction.

Model (see explain.md for the full derivation):

    N   = 1000                      (total population, conserved: S+E+I+R = N)
    sat = S * I / (N + I)           saturated incidence (same kernel that drives
                                    the exactly-recovered dS = -0.5 * sat)

    dI/dt = A * sat  +  B * sat * I / N  +  C * I

with
    A = +0.441026   (effective transmission into the infectious compartment)
    B = -1.818223   (higher-order saturation / crowding correction)
    C = -0.196788   (linear removal / recovery of infectives)

Equivalently written as a saturated force of infection with a crowding
correction minus linear recovery:

    dI/dt = A * (S*I/(N+I)) * (1 + (B/A) * I/N) + C * I
"""

# Total population (conserved throughout the experiment: S + E + I + R = N).
N = 1000.0

# Fitted constants (least squares on the full training trajectory).
A = 0.44102556444858465    # coefficient of  S*I/(N+I)
B = -1.818222986770873     # coefficient of  S*I^2 / (N*(N+I))
C = -0.19678775102130222   # coefficient of  I  (linear removal)


def _dI_dt(t, S, E, I, R):
    """Pointwise evaluation of the discovered law for a single state."""
    sat = S * I / (N + I)          # saturated incidence kernel
    return A * sat + B * sat * I / N + C * I


def law(input_data):
    """
    Map each input row independently to its dI_dt prediction.

    Parameters
    ----------
    input_data : list[dict[str, float]]
        Each dict has keys 't', 'S', 'E', 'I', 'R'. The verifier calls this
        with one row at a time, but a list of arbitrary length is supported.
        Rows are treated independently; ordering is irrelevant.

    Returns
    -------
    list[dict[str, float]]
        One dict per input row, each with the single key 'dI_dt'.
    """
    out = []
    for row in input_data:
        t = row.get("t", 0.0)
        S = row["S"]
        E = row.get("E", 0.0)
        I = row["I"]
        R = row.get("R", 0.0)
        out.append({"dI_dt": _dI_dt(t, S, E, I, R)})
    return out
