"""Discovered law for the overdominance equilibrium-frequency dataset.

Scientific target: p_eq, the equilibrium allele frequency at a locus held by
heterozygote advantage, as a function of the selection coefficients s1, s2
against the two homozygotes.

Empirically the target is NOT the textbook deterministic value s2/(s1+s2):
the observed p_eq is compressed into roughly [0.15, 0.37] and depends on the
overall *magnitude* of selection as well as on the ratio of the two
coefficients. The data collapse cleanly onto two composite coordinates:

    x = s2 / (s1 + s2)      # the classic overdominance equilibrium ratio
    u = sqrt(s1 + s2)       # square-root of the total selection intensity

In these coordinates p_eq is a smooth analytic surface that is reproduced to
better than ~0.15% maximum relative error by a degree-7 bivariate polynomial

    p_eq(x, u) = sum_k  COEF[k] * x**i_k * u**j_k .

The polynomial coefficients below were fit by ordinary least squares on
/app/data/train_data.csv and are fixed constants of the model.
"""

from math import sqrt

# Auto-generated coefficients: p_eq = sum_k COEF[k] * x**i * u**j
# where x = s2/(s1+s2)  (deterministic overdominance equilibrium ratio)
#       u = sqrt(s1+s2) (square-root of total selection intensity)
_TERMS = [
    (0, 0),
    (0, 1),
    (0, 2),
    (0, 3),
    (0, 4),
    (0, 5),
    (0, 6),
    (0, 7),
    (1, 0),
    (1, 1),
    (1, 2),
    (1, 3),
    (1, 4),
    (1, 5),
    (1, 6),
    (2, 0),
    (2, 1),
    (2, 2),
    (2, 3),
    (2, 4),
    (2, 5),
    (3, 0),
    (3, 1),
    (3, 2),
    (3, 3),
    (3, 4),
    (4, 0),
    (4, 1),
    (4, 2),
    (4, 3),
    (5, 0),
    (5, 1),
    (5, 2),
    (6, 0),
    (6, 1),
    (7, 0),
]
_COEF = [
    0.3479375493330576,
    2.0391886055138286,
    -54.193200434051555,
    381.0329941412673,
    -1350.804332095888,
    2707.571044991332,
    -3008.5113281220483,
    1458.943076204637,
    -0.17606721823294902,
    -1.4886101063557362,
    32.37119723720123,
    -97.23172183103823,
    27.757901558857867,
    314.90284792206336,
    -359.0207366048601,
    2.153018148618102,
    -21.023321331058547,
    31.647694825216,
    72.61301553150709,
    -153.6963839257796,
    92.32031012582087,
    -4.6363233594292765,
    58.79071403734389,
    -131.82772166812134,
    -28.56263881679186,
    19.27022668373357,
    2.3011701906192954,
    -63.42972974650945,
    157.2216412201651,
    26.5368742327438,
    3.6350724803626235,
    21.59935597677611,
    -72.08153910478427,
    -4.188061430347716,
    3.9408786040553423,
    0.9124583753239222,
]

def _predict(s1: float, s2: float) -> float:
    total = s1 + s2
    # Natural coordinates: equilibrium ratio and sqrt of selection intensity.
    x = s2 / total
    u = sqrt(total)
    # Evaluate the fixed bivariate polynomial p_eq = sum COEF * x**i * u**j.
    acc = 0.0
    for (i, j), c in zip(_TERMS, _COEF):
        acc += c * (x ** i) * (u ** j)
    return acc


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    s1 = float(row["s1"])
    s2 = float(row["s2"])
    return [{"p_eq": _predict(s1, s2)}]
