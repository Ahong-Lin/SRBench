def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict instantaneous acceleration (dv_dt) from position, velocity, and time.

    This implements a degree-3 polynomial model fitted to the training data.
    The model achieves R² = 0.9817 on the training set.

    Fitted polynomial:
    dv_dt = intercept + sum of polynomial terms up to degree 3 in (t, x, v)
    """
    result = []
    for row in input_data:
        t = row["t"]
        x = row["x"]
        v = row["v"]

        # Degree 3 polynomial model coefficients
        dv_dt = 0.3501910935  # intercept

        # Linear terms
        dv_dt += -0.0018601139 * t
        dv_dt += 0.2294377900 * x
        dv_dt += 0.4191890321 * v

        # Quadratic terms
        dv_dt += -0.0007094245 * (t**2)
        dv_dt += 0.0221310472 * (t * x)
        dv_dt += -0.0194561151 * (t * v)
        dv_dt += -0.1744280262 * (x**2)
        dv_dt += -0.0301024027 * (x * v)
        dv_dt += -0.1912823836 * (v**2)

        # Cubic terms
        dv_dt += 0.0000103186 * (t**3)
        dv_dt += -0.0003925933 * (t**2 * x)
        dv_dt += 0.0003344640 * (t**2 * v)
        dv_dt += 0.0063076200 * (t * x**2)
        dv_dt += 0.0007815450 * (t * x * v)
        dv_dt += 0.0076284778 * (t * v**2)
        dv_dt += -0.9686260850 * (x**3)
        dv_dt += -0.1438588227 * (x**2 * v)
        dv_dt += -0.0380785704 * (x * v**2)
        dv_dt += -0.0659835189 * (v**3)

        result.append({"dv_dt": dv_dt})

    return result
