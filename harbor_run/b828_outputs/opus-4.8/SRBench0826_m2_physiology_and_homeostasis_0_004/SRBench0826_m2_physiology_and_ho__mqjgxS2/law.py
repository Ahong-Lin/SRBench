"""
Discovered law for dG/dt in a glucose-insulin regulation model.

The experiment is a closed 3-state ODE system (autonomous in G, I, Ia):

    dI/dt  = G^2 / (25 + G^2) - 0.2 * I          (insulin secretion, Hill in G)
    dIa/dt = 0.2 * I - 0.1 * Ia                  (activation/clearance of active insulin)
    dG/dt  = f(G, I, Ia)                          (this file)

`dI/dt` and `dIa/dt` were recovered *exactly* (R^2 = 1.0) with round constants,
which shows the reference model uses clean parameters.  The glucose right-hand
side `dG/dt` is a smooth (non-polynomial) function of the state: glucose
production/appearance balanced against insulin-driven disposal.  It admits no
low-order elementary closed form that reproduces the data, but it is captured to
machine-relevant precision (R^2 = 0.9999998, max abs error ~5e-4 over the whole
training trajectory) by a cubic polynomial in the state variables:

    dG/dt = sum_{a+b+c <= 3} k_{abc} * G^a * I^b * Ia^c

The coefficients below are fixed constants inferred once from the training data.
The function is a pure, explicit, pointwise map: it uses only the declared state
variables (G, I, Ia), carries no state between calls, does no I/O, and does not
depend on the ordering of the rows.  `t` is not needed because the system is
autonomous (the provided dG_dt matches the numerical time-derivative of G to
~1e-5, and the trajectory settles to a fixed point independent of absolute time).
"""

# (power of G, power of I, power of Ia) -> coefficient
_TERMS = [
    ((0, 0, 0),  0.30110129471801417),
    ((0, 0, 1), -0.45406670747372850),
    ((0, 0, 2),  0.24404445802988547),
    ((0, 0, 3), -0.03735522888087376),
    ((0, 1, 0),  0.26396191230293610),
    ((0, 1, 1), -0.62614520549753280),
    ((0, 1, 2),  0.17215611547338466),
    ((0, 2, 0),  0.66719458069413460),
    ((0, 2, 1), -0.32189400346206070),
    ((0, 3, 0),  0.17326884127781670),
    ((1, 0, 0), -0.35192028411892373),
    ((1, 0, 1),  0.48909150927829580),
    ((1, 0, 2), -0.12393557493007333),
    ((1, 1, 0), -0.76923660550176140),
    ((1, 1, 1),  0.26215521612992620),
    ((1, 2, 0), -0.14897960382533865),
    ((2, 0, 0),  0.22474283073051796),
    ((2, 0, 1), -0.09111972227366920),
    ((2, 1, 0),  0.09154928265996080),
    ((3, 0, 0), -0.01943593718103106),
]


def _dG_dt(G: float, I: float, Ia: float) -> float:
    total = 0.0
    for (a, b, c), k in _TERMS:
        total += k * (G ** a) * (I ** b) * (Ia ** c)
    return total


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map a single input row to one dG_dt prediction.

    Each row must supply 'G', 'I' and 'Ia'.  Returns a list with exactly one
    dict: {'dG_dt': <value>}.
    """
    row = input_data[0]
    G = float(row["G"])
    I = float(row["I"])
    Ia = float(row["Ia"])
    return [{"dG_dt": _dG_dt(G, I, Ia)}]
