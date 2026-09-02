def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Generalized Holling Type III functional response.

    f = a * N^2 / (1 + b * N + c * N^2)

    At low prey density N the response rises quadratically (accelerating),
    then saturates as handling time limits intake at high density.
    Parameters fitted from the training data.
    """
    a = 1.006988761186352
    b = 1.074049257556507
    c = 0.7041530697040084

    row = input_data[0]
    N = row["N"]
    f = a * N * N / (1.0 + b * N + c * N * N)
    return [{"f": f}]
