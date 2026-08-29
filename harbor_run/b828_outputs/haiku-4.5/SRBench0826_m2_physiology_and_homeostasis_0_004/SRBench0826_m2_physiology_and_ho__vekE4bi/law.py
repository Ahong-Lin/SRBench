def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Compute dG_dt from glucose-insulin regulation dynamics.

    The relationship is a quadratic function of insulin (I), glucose (G),
    and active insulin (Ia):

    dG_dt = 0.16148944
            - 0.34093505 * I
            + 0.09259893 * G
            - 0.13084649 * Ia
            - 0.07404695 * I^2
            - 0.00382344 * G^2
            + 0.04835007 * Ia^2
    """
    results = []
    for row in input_data:
        I = row['I']
        G = row['G']
        Ia = row['Ia']

        dG_dt = (
            0.16148944
            - 0.34093505 * I
            + 0.09259893 * G
            - 0.13084649 * Ia
            - 0.07404695 * I * I
            - 0.00382344 * G * G
            + 0.04835007 * Ia * Ia
        )

        results.append({'dG_dt': dG_dt})

    return results
