def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discovers and applies the mathematical law for dv_dt in a damped harmonic oscillator system.

    The law is a quadratic polynomial in the state variables (x, v, z):
    dv_dt = c0 + c1*x + c2*v + c3*z + c4*x² + c5*v² + c6*z²

    Args:
        input_data: List with a single dictionary containing keys 't', 'x', 'v', 'z'

    Returns:
        List with a single dictionary containing the computed 'dv_dt' value
    """
    # Coefficients fitted from training data
    c0 = -0.283039425540822
    c1 = -2.741435514255184
    c2 = -0.977937732352161
    c3 = -1.126138834023231
    c4 = 0.497473097091927
    c5 = 0.146807150733700
    c6 = 0.037572370395163

    row = input_data[0]
    x = row['x']
    v = row['v']
    z = row['z']

    # Compute dv_dt using the discovered law
    dv_dt = (c0 +
             c1 * x +
             c2 * v +
             c3 * z +
             c4 * (x ** 2) +
             c5 * (v ** 2) +
             c6 * (z ** 2))

    return [{'dv_dt': dv_dt}]
