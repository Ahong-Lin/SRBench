def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dv_dt using a polynomial model of degree 2.

    Formula:
    dv_dt = 0.3195228729
            - 0.0421832546 * t
            - 2.1297804942 * x
            - 0.1749894077 * v
            + 0.0005947074 * t^2
            + 0.2528287932 * t*x
            - 0.3232217366 * t*v
            - 1.4268752324 * x^2
            - 1.3771172128 * x*v
            - 0.0888733966 * v^2
    """
    results = []

    for row in input_data:
        t = row['t']
        x = row['x']
        v = row['v']

        dv_dt = (
            0.3195228729
            - 0.0421832546 * t
            - 2.1297804942 * x
            - 0.1749894077 * v
            + 0.0005947074 * (t ** 2)
            + 0.2528287932 * t * x
            - 0.3232217366 * t * v
            - 1.4268752324 * (x ** 2)
            - 1.3771172128 * x * v
            - 0.0888733966 * (v ** 2)
        )

        results.append({'dv_dt': dv_dt})

    return results
