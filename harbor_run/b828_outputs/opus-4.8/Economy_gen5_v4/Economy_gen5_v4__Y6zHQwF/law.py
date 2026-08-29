import math


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts `dp` from the input variables using a discovered closed-form law.

    Discovered structure:
        dp = 0.2 * ( pi*tanh(dc) + tanh(dp_comp) + tanh(dc_acc) )   # saturating responses
             + polynomial base in dc (asymmetric, expanding)
             + weak dc*sigma_c damping term
             + constant

    sigma_c enters only through the small dc*sigma_c interaction.
    """
    # Coefficients fitted by linear least squares on the training data.
    K_PI_TANH_DC = 0.216158   # pi * tanh(dc)
    K_TANH_DPC   = 0.200506   # tanh(dp_comp)
    K_TANH_DCA   = 0.200158   # tanh(dc_acc)
    B1 = 0.015835   # dc
    B2 = 0.055524   # dc^2
    B3 = 0.199088   # dc^3
    B4 = -0.012986  # dc^4
    B5 = -0.030169  # dc^5
    K_DC_SC = -0.025702  # dc * sigma_c
    CONST = -0.005031

    out = []
    for r in input_data:
        dc = r["dc"]
        pi = r["pi"]
        dpc = r["dp_comp"]
        sc = r["sigma_c"]
        dca = r["dc_acc"]

        dp = (
            K_PI_TANH_DC * pi * math.tanh(dc)
            + K_TANH_DPC * math.tanh(dpc)
            + K_TANH_DCA * math.tanh(dca)
            + B1 * dc
            + B2 * dc**2
            + B3 * dc**3
            + B4 * dc**4
            + B5 * dc**5
            + K_DC_SC * dc * sc
            + CONST
        )
        out.append({"dp": dp})
    return out
