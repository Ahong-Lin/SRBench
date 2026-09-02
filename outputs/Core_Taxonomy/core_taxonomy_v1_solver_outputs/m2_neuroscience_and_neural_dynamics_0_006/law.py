import math


# --------------------------------------------------------------------------
# Discovered law: saturating (generalized-logistic) growth of conduction
# velocity with axon diameter.
#
#     v(d) = Vmax / (1 + exp(-P(ln d)))
#
# where P(u) is a 7th-degree polynomial in u = ln(d). The velocity rises
# steeply at small diameter (a power-law regime), passes through an
# inflection near d ~ 11, and saturates toward Vmax ~= 3.13 as internal
# resistance ceases to be the limiting factor.
#
# Parameters were fit to the noise-free training column `v`.
# --------------------------------------------------------------------------

VMAX = 3.126492946862683

# Polynomial coefficients for the log-odds P(u) = sum(COEF[i] * u**(deg-i)),
# highest power first (numpy.polyval convention), u = ln(d).
COEF = [
    -0.007967563257741644,   # u^7
     0.039776270485852444,   # u^6
    -0.019240768305736202,   # u^5
    -0.06591714085331225,    # u^4
     0.059808405689502804,   # u^3
    -0.3096498157321453,     # u^2
     2.3039608003993126,     # u^1
    -4.7865054893737,        # u^0
]


def _polyval(coef, x):
    result = 0.0
    for c in coef:
        result = result * x + c
    return result


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    d = row["d"]
    u = math.log(d)
    logit = _polyval(COEF, u)
    v = VMAX / (1.0 + math.exp(-logit))
    return [{"v": v}]
