"""Discovered law for the rate of loss of active enzyme, dE/dt.

Model (thermal inactivation of an enzyme with reversible unfolding plus
irreversible bimolecular aggregation of the native form):

    dE/dt = -k1 * E  -  k2 * E**2  +  kr * A

where
    E  = concentration of active (folded) enzyme
    A  = concentration of the reversibly-unfolded pool
    G  = accumulated aggregate (does not enter dE/dt directly)

Terms:
    -k1 * E    first-order thermal unfolding / inactivation of native enzyme
    -k2 * E**2 second-order (bimolecular) aggregation of native enzyme
    +kr * A    refolding of the reversibly-unfolded species back to active enzyme

Constants were inferred from the training data by linear least squares.
Note at the initial state (E=10, A=0): -k1*10 - k2*100 = -1.19 - 0.79 = -1.98,
matching the observed dE/dt(0) = -2.0.
"""

# Fixed constants inferred from the training data.
K1 = 0.11909839   # first-order native inactivation rate
K2 = 0.00787333   # second-order native aggregation rate
KR = 0.34568687   # refolding rate from the unfolded pool A


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Map each input row independently to one dE_dt prediction.

    Expects a list with exactly one dict having keys 't', 'E', 'A', 'G'.
    Returns a list with exactly one dict {'dE_dt': value}.
    """
    row = input_data[0]
    E = row["E"]
    A = row["A"]

    dE_dt = -K1 * E - K2 * E * E + KR * A
    return [{"dE_dt": dE_dt}]
