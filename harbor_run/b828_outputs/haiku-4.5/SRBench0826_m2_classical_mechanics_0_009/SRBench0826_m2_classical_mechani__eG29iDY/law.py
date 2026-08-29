def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dv_dt from the spring-mass system with cubic hardening.

    The discovered law is a polynomial regression with interaction terms:
    dv_dt = -4.0459 + 4.6190*x - 6.8354*x² + 4.8846*x³
            - 4.2943*z + 6.1382*e + 3.8264*z*x - 3.7547*e*x

    This model achieves R² = 0.9930 on the training data.
    """
    result = []

    # Coefficients from polynomial regression with interactions
    intercept = -4.0458887397
    coef_x = 4.6189677273
    coef_x2 = -6.8354303633
    coef_x3 = 4.8846258421
    coef_z = -4.2943098789
    coef_e = 6.1382101743
    coef_zx = 3.8264478493
    coef_ex = -3.7546904721

    for row in input_data:
        x = row['x']
        z = row['z']
        e = row['e']

        # Compute dv_dt using the polynomial model with interactions
        dv_dt = (intercept +
                 coef_x * x +
                 coef_x2 * x**2 +
                 coef_x3 * x**3 +
                 coef_z * z +
                 coef_e * e +
                 coef_zx * z * x +
                 coef_ex * e * x)

        result.append({'dv_dt': dv_dt})

    return result
