def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dv_dt from t, x, v using a polynomial model with cross terms.

    Model: dv_dt = a3*x^3 + a2*x^2 + a1*x + b1*v + b2*v^2 + c1*x*v + c2*x^2*v + c3*x*v^2 + const
    """
    # Coefficients learned from training data
    a3 = -2.2470084221
    a2 = -0.0104937311
    a1 = -0.0035488370
    b1 = -0.6901035531
    b2 = -0.0220520679
    c1 = -0.0859189315
    c2 = 0.1943519573
    c3 = -0.0798364190
    const = 0.0005097439

    result = []
    for row in input_data:
        x = row['x']
        v = row['v']

        dv_dt = (
            a3 * (x ** 3) +
            a2 * (x ** 2) +
            a1 * x +
            b1 * v +
            b2 * (v ** 2) +
            c1 * x * v +
            c2 * (x ** 2) * v +
            c3 * x * (v ** 2) +
            const
        )

        result.append({'dv_dt': dv_dt})

    return result
