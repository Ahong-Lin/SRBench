def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dv_dt for a damped harmonic oscillator system.

    The relationship is a polynomial model of degree 2 in the state variables (x, v, z):
    dv_dt = -0.7954883054*x + 0.1033550046*v + 1.4286187149*z
            - 1.7005066537*x² - 1.2444903543*x*v - 3.6905364693*x*z
            - 0.3454283624*v² - 1.2965000872*v*z - 2.1091009773*z²
            - 0.0612273670

    Args:
        input_data: A list containing exactly one dict with keys 't', 'x', 'v', 'z'

    Returns:
        A list containing exactly one dict with key 'dv_dt'
    """
    row = input_data[0]
    x = row['x']
    v = row['v']
    z = row['z']

    # Compute polynomial features
    x2 = x * x
    v2 = v * v
    z2 = z * z
    xv = x * v
    xz = x * z
    vz = v * z

    # Evaluate the polynomial
    dv_dt = (-0.7954883054 * x
             + 0.1033550046 * v
             + 1.4286187149 * z
             - 1.7005066537 * x2
             - 1.2444903543 * xv
             - 3.6905364693 * xz
             - 0.3454283624 * v2
             - 1.2965000872 * vz
             - 2.1091009773 * z2
             - 0.0612273670)

    return [{'dv_dt': dv_dt}]
