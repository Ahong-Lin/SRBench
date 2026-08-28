def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict Brier score from logC (logarithm of training compute) using a degree-20 polynomial fit.

    The model captures the non-monotonic relationship between compute and generalization error.
    """
    # Coefficients from polynomial fit (degree 20, highest degree first)
    coeffs = [
        3.216086548936672e-07,
        1.499900375905386e-07,
        -1.541291881386351e-05,
        -5.239071021710427e-06,
        3.172601355109437e-04,
        6.338283016284702e-05,
        -3.658482278020661e-03,
        -1.585312944830032e-04,
        2.580479661251892e-02,
        -3.433929447884086e-03,
        -1.136878241457374e-01,
        3.806878461479948e-02,
        3.036242759753934e-01,
        -1.735127426350171e-01,
        -4.396949007287045e-01,
        3.817062442050937e-01,
        2.265495692220347e-01,
        -3.174549160301878e-01,
        1.182827893699445e-01,
        -2.208642413332403e-02,
        1.502248801986036e-01,
    ]

    results = []
    for row in input_data:
        logC = row['logC']
        # Evaluate polynomial: sum(c_i * logC^(20-i))
        brier = sum(c * (logC ** (20 - i)) for i, c in enumerate(coeffs))
        results.append({"Brier": brier})

    return results
