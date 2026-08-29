import math

# ---------------------------------------------------------------------------
# Discovered law for dI/dt of a seasonally forced infection with an
# environmental pathogen reservoir C.
#
#   dI/dt = beta(t) * S * I                      (seasonally forced incidence)
#           + omega_I * R                        (waning immunity re-entering I)
#           - I * ( g + kI*I + kR*R              (state-dependent removal:
#                   + kC*C + kCC*C^2 )            recovery + load-driven mortality)
#
# with beta(t) = beta0 * (1 + beta1 * cos(2*pi*t/T)).
#
# The transmission block (beta0=3, beta0*beta1=0.9, omega_I=0.1) was pinned
# from the *exact* susceptible balance dS/dt = mu(1-S) + omega*R - beta(t)*S*I,
# which the data reproduces to ~1e-6.  The removal block was then fitted to the
# residual.  See explain.md for the full derivation.
# ---------------------------------------------------------------------------

# Seasonal forcing (fixed environmental inputs)
BETA0 = 3.021205466354669      # baseline transmission rate  (~3)
BETA_AMP = 0.899513056227309   # beta0*beta1 seasonal amplitude (~0.9)
PERIOD = 1.0                   # forcing period T (one year)
OMEGA = 2.0 * math.pi / PERIOD

# Waning immunity flux back into the infectious class
OMEGA_I = 0.1004378776366643   # (~0.1)

# State-dependent per-capita removal rate coefficients
G  = 1.1303403265908627        # constant recovery/removal
KI = 1.026426139837298         # crowding (I) term
KR = 0.9409156949186988        # recovered-density term
KC = 4.55254099769047          # environmental-load term
KCC = 4.146884111830586        # nonlinear environmental-load term


def _predict(row):
    t = row["t"]
    S = row["S"]
    I = row["I"]
    R = row["R"]
    C = row["C"]

    beta_t = BETA0 + BETA_AMP * math.cos(OMEGA * t)

    incidence = beta_t * S * I
    inflow = OMEGA_I * R
    removal = I * (G + KI * I + KR * R + KC * C + KCC * C * C)

    return incidence + inflow - removal


def law(input_data):
    """Map each input row independently to a dI_dt prediction.

    input_data: list of dicts with keys t, S, I, R, C
    returns:    list of dicts with key dI_dt
    """
    return [{"dI_dt": _predict(row)} for row in input_data]
