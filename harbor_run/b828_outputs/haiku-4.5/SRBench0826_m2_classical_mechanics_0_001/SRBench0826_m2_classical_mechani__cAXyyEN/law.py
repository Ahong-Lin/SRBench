def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discover and predict dv_dt for a damped harmonic oscillator system.

    The law was discovered through symbolic regression on training data from a
    damped spring-mass system with velocity-dependent viscous damping.

    Formula:
    dv_dt = -0.3147214789
            - 2.842061744655322*x
            - 1.041729221324466*v
            - 1.283927733163964*z
            + 0.001676485222091*t
            + 0.616865330197440*x²
            + 0.198272994170853*v²
            + 0.033491164926916*x*v
    """

    # Coefficients from linear regression with polynomial features
    intercept = -0.314721478895053
    coef_x = -2.842061744655322
    coef_v = -1.041729221324466
    coef_z = -1.283927733163964
    coef_t = 0.001676485222091
    coef_x2 = 0.616865330197440
    coef_v2 = 0.198272994170853
    coef_xv = 0.033491164926916

    result = []
    for row in input_data:
        t = row['t']
        x = row['x']
        v = row['v']
        z = row['z']

        # Compute dv_dt using the discovered formula
        dv_dt = (intercept
                + coef_x * x
                + coef_v * v
                + coef_z * z
                + coef_t * t
                + coef_x2 * x * x
                + coef_v2 * v * v
                + coef_xv * x * v)

        result.append({'dv_dt': dv_dt})

    return result
