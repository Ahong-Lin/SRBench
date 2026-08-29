def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discovered mathematical law for glucose-insulin regulation system.

    This implements a degree-2 polynomial model that predicts dG_dt
    (instantaneous rate of glucose change) from plasma glucose (G),
    plasma insulin (I), active insulin (Ia), and time (t).

    The model was discovered through polynomial regression on experimental
    glucose-insulin kinetics data. The relationship captures the feedback
    dynamics where insulin suppresses glucose production and promotes uptake.
    """
    result = []
    for row in input_data:
        t = row['t']
        G = row['G']
        I = row['I']
        Ia = row['Ia']

        # Quadratic polynomial model fitted to training data
        # Terms ordered by importance: linear, quadratic cross-terms, quadratic diagonal
        dG_dt = (
            0.2643102857                          # intercept
            - 0.0035892896 * t                    # linear time dependence
            + 0.0157191426 * G                    # linear glucose feedback
            - 0.1836508811 * I                    # linear insulin effect (dominant)
            - 0.2219280725 * Ia                   # linear active insulin effect
            + 0.0000206762 * t**2                 # quadratic time
            + 0.0011344179 * t * G                # t-G interaction
            - 0.0027791191 * t * I                # t-I interaction
            + 0.0000684611 * t * Ia               # t-Ia interaction
            + 0.0030259911 * G**2                 # quadratic glucose
            - 0.0173228984 * G * I                # G-I interaction
            + 0.0822059697 * G * Ia               # G-Ia interaction
            - 0.1973832496 * I**2                 # quadratic insulin (strong negative feedback)
            - 0.0059630161 * I * Ia               # I-Ia interaction
            + 0.0674526351 * Ia**2                # quadratic active insulin
        )

        result.append({'dG_dt': dG_dt})

    return result
