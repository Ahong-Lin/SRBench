def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discovered law for quantum tunneling in a double-well configuration.

    The rate of probability transfer between wells is governed by:
    dPr/dt = K*N - 0.1*Pr + 0.05

    Where:
    - K is the effective coupling parameter (varies with position/phase)
    - N is a decay/normalization factor
    - Pr is the current probability in the second well
    """
    result = []
    for row in input_data:
        K = row["K"]
        N = row["N"]
        Pr = row["Pr"]

        # Compute dPr_dt using the discovered formula
        dPr_dt = K * N - 0.1 * Pr + 0.05

        result.append({"dPr_dt": dPr_dt})

    return result
