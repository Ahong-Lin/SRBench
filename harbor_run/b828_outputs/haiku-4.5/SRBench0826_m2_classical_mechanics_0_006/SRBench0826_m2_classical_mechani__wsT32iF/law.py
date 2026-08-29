import math

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Computes the time derivative of x-velocity (dvx_dt) for a body orbiting
    under gravitational attraction.

    The discovered physical law: dvx_dt = -GM * x / r³
    where r = sqrt(x² + y²) is the distance from the central body.

    GM ≈ 0.981038581637830 (gravitational parameter)
    """
    GM = 0.981038581637830

    result = []
    for row in input_data:
        x = row['x']
        y = row['y']

        # Compute distance from center
        r_squared = x * x + y * y
        r = math.sqrt(r_squared)

        # Apply Newton's law of gravitation: a = -GM * r_hat / r²
        # For the x-component: dvx_dt = -GM * x / r³
        r_cubed = r_squared * r
        dvx_dt = -GM * x / r_cubed

        result.append({'dvx_dt': dvx_dt})

    return result
