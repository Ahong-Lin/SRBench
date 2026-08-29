import math


# Coefficients fitted on /app/data/train_data.csv (least squares).
# Model:
#   dp = P(dc, pi) + 0.2005*tanh(dp_comp) + 0.2003*tanh(dc_acc)
#        + dc_sc*(dc*sigma_c) + intercept
# where P(dc, pi) is a low-order polynomial in dc modulated by pi.
_C = {
    "dc": 0.01785743716226052,
    "dc_pi": 0.24188712164717116,
    "dc_pi2": -0.05776126000507095,
    "dc2": 0.05137645509069636,
    "dc3": 0.1854553211439348,
    "dc4": -0.01270863893499966,
    "dc5": -0.027413159071366735,
    "dc2_pi": 0.0071451627849374744,
    "dc3_pi": -0.01945938996176296,
    "tdpc": 0.20049658070218987,
    "tdca": 0.20031210122662813,
    "dc_sc": -0.02575735575144516,
    "intercept": -0.004887315403871259,
}


def _predict(dc, pi, dp_comp, sigma_c, dc_acc):
    dc2 = dc * dc
    dc3 = dc2 * dc
    dc4 = dc3 * dc
    dc5 = dc4 * dc
    return (
        _C["dc"] * dc
        + _C["dc_pi"] * dc * pi
        + _C["dc_pi2"] * dc * pi * pi
        + _C["dc2"] * dc2
        + _C["dc3"] * dc3
        + _C["dc4"] * dc4
        + _C["dc5"] * dc5
        + _C["dc2_pi"] * dc2 * pi
        + _C["dc3_pi"] * dc3 * pi
        + _C["tdpc"] * math.tanh(dp_comp)
        + _C["tdca"] * math.tanh(dc_acc)
        + _C["dc_sc"] * dc * sigma_c
        + _C["intercept"]
    )


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the output variable based on the input variables according to a discovered law.

    Args:
        input_data: A list of dictionaries, where each dictionary is a single data
                    point containing the input variable names
                    ('dc', 'pi', 'dp_comp', 'sigma_c', 'dc_acc') as keys and their
                    corresponding values.

    Returns:
        A list of dictionaries, corresponding to the input_data list, with each
        dictionary containing the predicted output variable, e.g. {"dp": value}.
    """
    out = []
    for row in input_data:
        dp = _predict(
            row["dc"],
            row["pi"],
            row["dp_comp"],
            row["sigma_c"],
            row["dc_acc"],
        )
        out.append({"dp": dp})
    return out
