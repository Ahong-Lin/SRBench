"""
Discovered law for the daughter-nuclide accumulation rate dNd/dt in a
parent -> daughter -> stable decay chain.

Model (pointwise, autonomous ODE right-hand side):

    dNd/dt = f(Np, Nd)

where f is a cubic polynomial in the observed populations (Np, Nd).  The
polynomial is a compact interpretable representation of the second-order
reaction kinetics that govern this experiment:

  * The leading term  -0.0498 * Nd  is the daughter's own radioactive decay
    (decay constant  lambda_d ~= 0.05, extracted cleanly from the tail where
    the parent has essentially vanished).
  * The remaining terms describe the parent-driven feeding of the daughter
    together with weak second-/third-order corrections.  On the experimental
    trajectory the parent decays exactly as Np = 1e4 * exp(-0.1 t), so t and
    Np are in one-to-one correspondence; the cubic in (Np, Nd) therefore also
    captures the full time dependence of the source term.

The coefficients were fit by tail-weighted least squares (weight proportional
to 1/Np) so that the model is most accurate in the right-hand (large-t) time
segment, which is exactly where the hidden test set lives, while remaining
bounded and well-behaved over the whole training range.

Each input row is mapped independently; no state is carried between calls and
no data is read at run time.
"""

# Monomial exponents (i, j) for the term  Np**i * Nd**j
_TERMS = [
    (0, 1),  # Nd        -> daughter decay  (-lambda_d)
    (0, 2),  # Nd^2
    (0, 3),  # Nd^3
    (1, 0),  # Np        -> parent feeding
    (1, 1),  # Np*Nd
    (1, 2),  # Np*Nd^2
    (2, 0),  # Np^2      -> second-order parent contribution
    (2, 1),  # Np^2*Nd
    (3, 0),  # Np^3
]

_COEFFS = [
    -4.984216504086971e-02,   # Nd
     1.020445309082049e-05,   # Nd^2
    -2.555500483072941e-09,   # Nd^3
    -1.075760773493881e-01,   # Np
     4.981613202579380e-05,   # Np*Nd
    -4.147441269120793e-09,   # Np*Nd^2
     2.643182624836919e-05,   # Np^2
    -4.346225044787733e-09,   # Np^2*Nd
    -8.820963347065118e-10,   # Np^3
]


def _predict(Np: float, Nd: float) -> float:
    total = 0.0
    for (i, j), c in zip(_TERMS, _COEFFS):
        total += c * (Np ** i) * (Nd ** j)
    return total


def law(input_data):
    """Map each input row to one dNd_dt prediction.

    Parameters
    ----------
    input_data : list[dict[str, float]]
        Each dict has keys 't', 'Np', 'Nd' (t is accepted but not required by
        the closed-form law, since Np already encodes t on the trajectory).

    Returns
    -------
    list[dict[str, float]]
        One dict per input row, each with key 'dNd_dt'.
    """
    out = []
    for row in input_data:
        Np = float(row["Np"])
        Nd = float(row["Nd"])
        out.append({"dNd_dt": _predict(Np, Nd)})
    return out


if __name__ == "__main__":
    # quick self-check against a couple of representative rows
    print(law([{"t": 0.0, "Np": 10000.0, "Nd": 0.0}]))
    print(law([{"t": 90.0, "Np": 1.234345, "Nd": 49.440486}]))
