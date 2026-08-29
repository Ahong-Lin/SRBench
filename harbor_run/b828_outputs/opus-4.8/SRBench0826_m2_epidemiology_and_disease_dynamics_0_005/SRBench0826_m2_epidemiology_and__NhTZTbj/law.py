"""
Discovered law for a seasonally forced infection model.

Target: the instantaneous right-hand side dI/dt of the infectious compartment.

Discovered relationship (seasonally forced transmission with density-dependent
removal and an immunity-coupling feedback):

    dI/dt = beta(t) * S * I  -  gamma * I  -  eps * I * C  +  rho * R

with a periodic (seasonal) transmission rate

    beta(t) = b0 * (1 + alpha * cos(2*pi*t + phi))

All constants below were fit on the training trajectory. The seasonal
period is exactly 1 (angular frequency 2*pi), matching the yearly
environmental forcing described in the problem.

Each row is mapped independently; no state is carried between calls.
"""

import math

# Angular frequency of the environmental (seasonal) forcing: period = 1.
OMEGA = 2.0 * math.pi

# Fitted constants (from /app/data/train_data.csv, full-data least squares).
B0 = 1.514537      # baseline transmission scale
ALPHA = 0.593513   # relative seasonal forcing amplitude  (B0*ALPHA = 0.8989)
PHI = 0.026288     # small phase offset of the seasonal cycle
GAMMA = 0.475141   # linear per-capita removal (recovery/mortality) of infectives
EPS = 6.985162     # extra removal of infectives proportional to burden C
RHO = 0.095145     # immunity-coupling feedback from the recovered pool R


def _predict(t: float, S: float, I: float, R: float, C: float) -> float:
    beta = B0 * (1.0 + ALPHA * math.cos(OMEGA * t + PHI))
    return beta * S * I - GAMMA * I - EPS * I * C + RHO * R


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row to one dI_dt prediction.

    Parameters
    ----------
    input_data : list of dict
        Each dict has keys 't', 'S', 'I', 'R', 'C'.

    Returns
    -------
    list of dict
        One dict per input row with the single key 'dI_dt'.
    """
    out = []
    for row in input_data:
        t = float(row["t"])
        S = float(row["S"])
        I = float(row["I"])
        R = float(row["R"])
        C = float(row["C"])
        out.append({"dI_dt": _predict(t, S, I, R, C)})
    return out
