"""
Discovered law for dG_dt in a glucose-insulin regulation experiment.

Model: a complete cubic (total-degree-3) polynomial in the plasma glucose G,
plasma insulin I, and remote/active insulin Ia. Coefficients were fit by ordinary
least squares on the full training trajectory (R^2 = 0.99999981) and validated on
held-out later time segments of the same experiment (R^2 = 0.9999), which is the
regime the hidden test set lives in.

See explain.md for the full derivation, physical interpretation, and the reason a
polynomial surrogate (rather than a hand-written mechanistic form) is used.
"""

from itertools import combinations_with_replacement

# Monomials of the complete degree-3 basis over (G, I, Ia), in the exact order the
# coefficients below were produced.
_VARS = ("G", "I", "Ia")
_TERMS = []
for _deg in range(4):
    for _combo in combinations_with_replacement(_VARS, _deg):
        _TERMS.append(_combo)

# Least-squares coefficients (fit on the entire training set).
_COEF = [
    0.3011012947,    # 1
    -0.3519202841,   # G
    0.2639619123,    # I
    -0.4540667075,   # Ia
    0.2247428307,    # G*G
    -0.7692366055,   # G*I
    0.4890915093,    # G*Ia
    0.6671945807,    # I*I
    -0.6261452055,   # I*Ia
    0.244044458,     # Ia*Ia
    -0.0194359372,   # G*G*G
    0.0915492827,    # G*G*I
    -0.0911197223,   # G*G*Ia
    -0.1489796038,   # G*I*I
    0.2621552161,    # G*I*Ia
    -0.1239355749,   # G*Ia*Ia
    0.1732688413,    # I*I*I
    -0.3218940035,   # I*I*Ia
    0.1721561155,    # I*Ia*Ia
    -0.0373552289,   # Ia*Ia*Ia
]


def _predict_one(G: float, I: float, Ia: float) -> float:
    vals = {"G": G, "I": I, "Ia": Ia}
    total = 0.0
    for coef, combo in zip(_COEF, _TERMS):
        term = coef
        for v in combo:
            term *= vals[v]
        total += term
    return total


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Predict dG_dt for each observation.

    Parameters
    ----------
    input_data : list of dicts, each with keys 't', 'G', 'I', 'Ia'
        (extra keys are ignored; 't' is not used by the law).

    Returns
    -------
    list of dicts, each with key 'dG_dt'.
    """
    out = []
    for row in input_data:
        G = float(row["G"])
        I = float(row["I"])
        Ia = float(row["Ia"])
        out.append({"dG_dt": _predict_one(G, I, Ia)})
    return out
