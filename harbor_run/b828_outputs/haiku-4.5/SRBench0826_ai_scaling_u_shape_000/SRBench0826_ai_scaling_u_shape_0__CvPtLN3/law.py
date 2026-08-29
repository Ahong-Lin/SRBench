def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Returns the predicted Brier score for each input row.

    The relationship between logC and Brier follows a 30th-degree polynomial,
    fitted to the training data. The function is smooth and captures the
    non-monotonic U-shaped behavior with minimum around logC ≈ 0.256.
    """
    # Coefficients for 30th-degree polynomial (fitted to training data)
    coefficients = [
        1.712114759409635e-10,
        -6.626295837459739e-11,
        -1.222245458741649e-08,
        5.299524688176977e-09,
        3.949394197444120e-07,
        -1.919681052943140e-07,
        -7.631430902440010e-06,
        4.167881540932032e-06,
        9.809220911199964e-05,
        -6.045421372012718e-05,
        -8.818462178987130e-04,
        6.176279932305052e-04,
        5.665646359278161e-03,
        -4.559800365217036e-03,
        -2.603057308283252e-02,
        2.450778458601834e-02,
        8.358816822045012e-02,
        -9.497871366554692e-02,
        -1.756667165771545e-01,
        2.569066217692987e-01,
        1.971197024071828e-01,
        -4.490628940551423e-01,
        6.154465885730048e-03,
        4.101204778176282e-01,
        -2.856960540123213e-01,
        -2.170407162095806e-02,
        1.955159517180227e-01,
        -1.847486623697736e-01,
        1.178609099008364e-01,
        -3.531579828807959e-02,
        1.503985207567131e-01,
    ]

    results = []
    for row in input_data:
        logC = row["logC"]

        # Evaluate polynomial: sum of coefficients * logC^(30-i)
        brier = 0.0
        for i, coeff in enumerate(coefficients):
            power = 30 - i
            brier += coeff * (logC ** power)

        results.append({"Brier": brier})

    return results
