"""Discovered law for the rate of active-enzyme change during thermal inactivation.

Model (mass-action kinetics of thermal enzyme deactivation):

    dE/dt = -k_u * E  +  k_f * A  -  k_agg * E**2

    where
        E   = concentration of active (natively folded) enzyme
        A   = concentration of the reversibly unfolded / inactive intermediate
        k_u   unfolding rate         (native -> unfolded)
        k_f   refolding rate         (unfolded -> native)
        k_agg irreversible aggregation of native enzyme (2 E -> aggregate)

Fitted on /app/data/train_data.csv (R^2 = 0.99990, RMSE = 0.0039).
G (the accumulated aggregate) does not enter the rate of active enzyme
to any measurable degree, so it is intentionally omitted.
"""

# Coefficients obtained by least-squares on the full training set.
K_U = 0.11909838748808137   # effective linear loss of active enzyme (unfolding + net)
K_F = 0.3456868740850235    # refolding gain from the unfolded pool A
K_AGG = 0.007873326162044945  # second-order native aggregation


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Predict dE_dt for each observation.

    Parameters
    ----------
    input_data : list of dicts, each with keys 't', 'E', 'A', 'G'.

    Returns
    -------
    list of dicts, each with key 'dE_dt'.
    """
    results = []
    for row in input_data:
        E = row["E"]
        A = row["A"]
        dE_dt = -K_U * E + K_F * A - K_AGG * E * E
        results.append({"dE_dt": dE_dt})
    return results
