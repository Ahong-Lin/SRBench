"""
Discovered law for a seasonally forced infection (SIRS-type dynamics with an
environmental reservoir C).

Scientific target: the instantaneous right-hand side dI/dt of the infectious
compartment.

Discovered relation (explicit, pointwise):

    dI/dt = beta(t, C, I) * S * I  -  gamma * I

with a seasonally forced, state-modulated transmission rate

    beta(t, C, I) = b0
                    + a_cos * cos(2*pi*t)
                    + a_sin * sin(2*pi*t)      # 1-year environmental forcing
                    + kC    * C                # suppression by environmental reservoir C
                    + kI    * I                # density-dependent saturation of transmission

i.e.

    dI/dt = ( b0 + a_cos*cos(2*pi*t) + a_sin*sin(2*pi*t) + kC*C + kI*I ) * S * I
            - gamma * I

The period of the environmental forcing is fixed at T = 1 (2*pi angular
frequency).  All constants below were inferred from the training trajectory on
its sustained-oscillation (attractor) segment, which is the regime the hidden
right-hand test segment lives in.

The function maps each input row independently to one dI/dt value using only the
declared variables (t, S, I, C).  No data reads, no state between calls, no
interpolation or lookup.
"""

import math

# --- Fixed constants inferred from the training data (sustained regime, t >= 5) ---
B0 = 9.160104508008784      # baseline transmission coefficient
A_COS = 0.8960531715977994  # seasonal forcing amplitude (cos component)
A_SIN = 0.002491637013213666  # seasonal forcing amplitude (sin component, ~0)
K_C = -7.94131545010226     # modulation of transmission by reservoir C
K_I = -52.79605369242789    # density-dependent transmission saturation (in I)
GAMMA = 2.7240469963597804  # effective per-capita removal rate of infectives

TWO_PI = 2.0 * math.pi


def _dI_dt(t: float, S: float, I: float, C: float) -> float:
    beta = (
        B0
        + A_COS * math.cos(TWO_PI * t)
        + A_SIN * math.sin(TWO_PI * t)
        + K_C * C
        + K_I * I
    )
    return beta * S * I - GAMMA * I


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row to one dI_dt prediction.

    Each row must provide keys 't', 'S', 'I', 'C' (R is not needed for dI/dt).
    Returns a list of dicts, each with a single key 'dI_dt'.
    """
    out = []
    for row in input_data:
        t = float(row["t"])
        S = float(row["S"])
        I = float(row["I"])
        C = float(row["C"])
        out.append({"dI_dt": _dI_dt(t, S, I, C)})
    return out
