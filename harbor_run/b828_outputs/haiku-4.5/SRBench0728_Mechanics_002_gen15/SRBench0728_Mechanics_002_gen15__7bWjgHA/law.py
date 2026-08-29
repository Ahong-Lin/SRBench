def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dvx_dt using a degree-2 polynomial model fitted on (x, y, vx, vy).

    Coefficients were determined via least-squares fitting on the training data.
    The model captures the nonlinear dynamics of what appears to be a
    charged particle in a potential field or a forced oscillator.
    """
    results = []

    for row in input_data:
        x = row['x']
        y = row['y']
        vx = row['vx']
        vy = row['vy']

        # Degree-2 polynomial model coefficients (fitted on training data)
        dvx_dt = (
            -7.77863046 * vx**2
            - 5.95797866 * y * vx
            - 2.87141052 * vx * vy
            + 1.98645460 * x * vx
            - 1.36990664 * vy**2
            - 1.20053497 * vy
            - 1.13577808 * y**2
            + 1.04998489 * x * vy
            - 0.75492088 * y * vy
            + 0.64662453 * x * y
            + 0.53516555 * vx
            + 0.32990853 * x
            + 0.22800864 * y
            - 0.21094224 * x**2
            + 0.02677439
        )

        results.append({"dvx_dt": dvx_dt})

    return results
