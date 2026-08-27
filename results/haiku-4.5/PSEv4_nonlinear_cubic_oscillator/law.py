def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dv_dt from t, x, v using a polynomial regression model.

    Model coefficients (trained on full dataset):
    dv_dt = c0 + c1*x + c2*x² + c3*v + c4*v² + c5*x*v + c6*v³ + c7*x*v² + c8*t + c9*v*t
    """
    # Model coefficients
    c0 = 0.35524120
    c1 = -1.79791840
    c2 = -1.62634119
    c3 = -1.02689260
    c4 = -3.47935642
    c5 = -1.78357033
    c6 = -2.62607343
    c7 = -0.88346876
    c8 = -0.00779682
    c9 = -0.17803753

    results = []
    for item in input_data:
        t = item['t']
        x = item['x']
        v = item['v']

        # Compute polynomial features
        x_sq = x * x
        v_sq = v * v
        x_v = x * v
        v_cu = v * v * v
        x_v_sq = x * v_sq
        v_t = v * t

        # Compute prediction
        dv_dt = (c0 + c1*x + c2*x_sq + c3*v + c4*v_sq +
                 c5*x_v + c6*v_cu + c7*x_v_sq + c8*t + c9*v_t)

        results.append({'dv_dt': dv_dt})

    return results
