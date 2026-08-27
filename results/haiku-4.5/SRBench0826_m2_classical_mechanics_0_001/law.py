def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dv_dt for a damped harmonic oscillator.

    The discovered law: dv_dt = -2.0555265244 * x - 0.4905489105 * v - 0.2010093381

    This represents the acceleration of a mass on a spring in a viscous medium:
    - The -2.0555*x term is the spring restoring force (Hooke's law)
    - The -0.4905*v term is the velocity-dependent damping force
    - The -0.2010 intercept represents a constant force or systematic offset
    """
    result = []
    for data_point in input_data:
        x = data_point['x']
        v = data_point['v']

        dv_dt = -2.0555265244 * x - 0.4905489105 * v - 0.2010093381

        result.append({
            'dv_dt': dv_dt
        })

    return result
