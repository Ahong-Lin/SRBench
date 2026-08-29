import math

# ---------------------------------------------------------------------------
# Discovered law for the instantaneous right-hand side dN/dt of an observed,
# seasonally-forced population dynamical system.
#
#   dN/dt = c(t) + a(t)*N + b(t)*R + p*N^2 + q*R^2 + r*N*R
#
# where R = reproductive_adult_abundance, the seasonal forcing has an angular
# frequency w = 2*pi (a fundamental period of exactly 1 time unit), and
#
#   c(t) = c0 + sum_k [cc_k cos(k w t) + cs_k sin(k w t)]
#   a(t) = a0 + sum_k [ac_k cos(k w t) + as_k sin(k w t)]
#   b(t) = b0 + sum_k [bc_k cos(k w t) + bs_k sin(k w t)]
#
# The model is LINEAR in the state variables (N, R) with periodic coefficients
# plus small CONSTANT density-dependent (quadratic) competition terms. This
# form was selected because it extrapolates robustly to future time windows
# (unlike models with seasonally-modulated quadratic terms, which overfit).
# ---------------------------------------------------------------------------

W = 2.0 * math.pi  # seasonal angular frequency (period = 1 time unit)
K = 7              # number of Fourier harmonics in the seasonal coefficients

# Fitted coefficients (least squares on the full training set).
# Layout: [const, N, R, N^2, R^2, N*R] followed by 7 harmonic blocks, each
# block = [cos, sin, N*cos, N*sin, R*cos, R*sin].
COEF = [
    -36.8316888623879, 1.0442218422477916, -0.20287233069485922,
    0.003770691680345828, 0.03192895735051257, -0.032356767252308696,
    24.14756243535406, 17.885364659266166, -0.009725306732836794,
    -0.18449127295677234, 0.014960599714722855, 0.6706318881359077,
    -7.10417164367128, 8.605025959446488, 0.10612847937940195,
    -0.018579991771114607, -0.25598964349098025, 0.058084594776750986,
    -1.9471996825646598, -7.726781739073311, 0.025926453004722516,
    0.051600018807898745, -0.01660367371794025, -0.1403287742734558,
    3.537472584815328, -0.6810044670305384, -0.004653222468994134,
    0.005128415549640053, 0.0421964071246439, -0.0008070656395968712,
    0.08602525865839716, 1.5386807534115419, 0.015666873320790087,
    -0.012701307843393295, -0.02306332205959727, 0.03249006546844413,
    -0.662341093565368, 0.1517088380307335, 0.018417014198065074,
    -0.007367544920352742, -0.03072194873057832, 0.008657877200374031,
    -0.03855146383258479, -0.14023466160740616, -0.007743337759411162,
    -0.014949321345117728, 0.011603222399065083, 0.019171048723776618,
]


def _features(t, N, R):
    """Build the design vector matching the layout of COEF."""
    feats = [1.0, N, R, N * N, R * R, N * R]
    for k in range(1, K + 1):
        c = math.cos(k * W * t)
        s = math.sin(k * W * t)
        feats.extend([c, s, N * c, N * s, R * c, R * s])
    return feats


def law(input_data):
    """Map each input row independently to one {"dN_dt": prediction} dict."""
    out = []
    for row in input_data:
        t = float(row["t"])
        N = float(row["N"])
        R = float(row["reproductive_adult_abundance"])
        feats = _features(t, N, R)
        val = 0.0
        for f, c in zip(feats, COEF):
            val += f * c
        out.append({"dN_dt": val})
    return out
