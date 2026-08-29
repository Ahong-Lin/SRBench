"""
Discovered growth law for contact-inhibited mammalian cell culture.

Target (instantaneous right-hand side of the cell-count ODE):

    dN/dt = r * N * (A - b*N) / (A + h)

Interpretation (resource/space-limited proliferation with crowding):
  - Cells proliferate at a per-capita rate that is Monod-saturated in the
    locally available attachment resource A:  A / (A + h).
  - That available resource is discounted by a crowding term (b*N): as the
    population grows, the effective space/resource per usable site falls, and
    net division stops (dN/dt -> 0) once A = b*N, i.e. at confluence.

Fitted constants (from /app/data/train_data.csv, full trajectory):
    r = 5.34492e-02      intrinsic proliferation scale  [1/time]
    b = 4.03871e-05      crowding / space-consumption coefficient
    h = 8.25512          half-saturation constant for resource A

The relationship is pointwise: it maps a single (t, N, S, A) observation to
one dN/dt value using only the declared variables N and A plus fixed
constants.  (t and S are accepted but not needed - see explain.md.)
"""

# --- fixed constants inferred from the training data ---
R = 5.34492e-02
B = 4.03871e-05
H = 8.25512


def _dN_dt(N: float, A: float) -> float:
    """Instantaneous growth rate for one state (N, A)."""
    return R * N * (A - B * N) / (A + H)


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to a dN_dt prediction.

    Parameters
    ----------
    input_data : list of dict
        Each dict has keys 't', 'N', 'S', 'A' (floats).  The verifier calls
        this with exactly one row at a time, in arbitrary order.

    Returns
    -------
    list of dict
        One dict per input row, each with a single key 'dN_dt'.
    """
    out = []
    for row in input_data:
        N = float(row["N"])
        A = float(row["A"])
        out.append({"dN_dt": _dN_dt(N, A)})
    return out
