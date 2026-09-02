import math

# ---------------------------------------------------------------------------
# Discovered law for dispersal-driven spatial equilibrium abundance N_eq(c, r).
#
# Backbone (interpretable form):
#     N_eq = K / (1 + exp(-L)),      K = 100  (carrying capacity ceiling)
#     L    = ln( N_eq / (K - N_eq) )
#
# Empirically, in logit space L is very well described by a smooth surface that
# is dominated by  L ~ 0.75 * ln(r) + I(c),  i.e. a Hill/logistic response in
# the local growth rate r with exponent ~3/4, whose half-saturation point rises
# with connectivity c (more connected patches need larger r to fill up).  Small
# residual curvature in ln(r) and a weak ln(c) dependence are captured by the
# polynomial expansion below in the variables:
#         x = ln(r)          (log growth rate)
#         u = 1 / (c + 0.2)   (inverse connectivity, regularised)
#         w = ln(c)          (log connectivity)
#
# The sigmoid guarantees 0 < N_eq < 100 for every input.
# ---------------------------------------------------------------------------

_K = 100.0

# Coefficients fitted by least squares on the training set (logit target).
# Ordering matches _features() below.
_COEF = [-0.9332996554660974, 3.5224556309435293, -1.3321316813751976,
         0.5095152860971617, -0.10367745899401117, 0.00984135341572329,
         0.877180558690183, -0.2219412996481216, 0.05469013988512501,
         -0.009108359419232982, 0.00014359748967055495, 0.043602643854237226,
         0.041922743740565864, -0.011223450682807046, 0.001059068884620696,
         0.01912336737300696, -0.013305307710982187, 0.0002037389946110308,
         -0.0036142732930058595, -0.0038808777469836408, -0.0012743048784763292,
         0.9702297973172063, -0.15516979745907022, -0.0852385677270288,
         0.012691801012256265, -0.00804175612127576, 0.0009039068203443749]


def _features(x, u, w):
    """Build the feature vector (matches the order used when fitting)."""
    feats = []
    for i in range(6):
        xi = x ** i
        for j in range(6):
            if i + j <= 5:
                feats.append(xi * (u ** j))
    for i in range(3):
        xi = x ** i
        feats.append(xi * w)
        feats.append(xi * (w * w))
    return feats


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    row = input_data[0]
    c = float(row["c"])
    r = float(row["r"])

    # Guard against non-positive inputs (domain is c > 0, r > 0).
    c_safe = c if c > 1e-12 else 1e-12
    r_safe = r if r > 1e-12 else 1e-12

    x = math.log(r_safe)          # ln(growth rate)
    u = 1.0 / (c_safe + 0.2)      # regularised inverse connectivity
    w = math.log(c_safe)          # ln(connectivity)

    feats = _features(x, u, w)
    L = sum(a * f for a, f in zip(_COEF, feats))

    # Bounded logistic response -> N_eq in (0, K).
    if L >= 0:
        n_eq = _K / (1.0 + math.exp(-L))
    else:
        e = math.exp(L)
        n_eq = _K * e / (1.0 + e)

    return [{"N_eq": n_eq}]
