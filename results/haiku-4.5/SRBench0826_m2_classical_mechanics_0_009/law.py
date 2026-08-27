def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dv/dt for a Duffing oscillator with nonlinear hardening.

    Physics: A mass on a nonlinear spring with restoring force F = -k*x - alpha*x^3
    plus amplitude-dependent effects captured by auxiliary variables z and e.

    Model: dv/dt = -3.0606*x + 1.4341*x³ - 0.2401*v + 0.7307*z + 1.2621*z² + 0.1224*e

    where:
    - x: displacement
    - v: velocity
    - z: auxiliary variable (appears correlated with higher-order inertial effects)
    - e: auxiliary variable (energy-like quantity affecting acceleration)
    """
    coeffs = {
        'x': -3.0606096950,
        'x3': 1.4340888181,
        'v': -0.2401400172,
        'z': 0.7306711973,
        'z2': 1.2621190238,
        'e': 0.1224467195,
    }

    results = []
    for row in input_data:
        x = row['x']
        v = row['v']
        z = row['z']
        e = row['e']

        dv_dt = (
            coeffs['x'] * x +
            coeffs['x3'] * (x ** 3) +
            coeffs['v'] * v +
            coeffs['z'] * z +
            coeffs['z2'] * (z ** 2) +
            coeffs['e'] * e
        )

        results.append({'dv_dt': dv_dt})

    return results
