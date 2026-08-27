import math

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dvx_dt (acceleration in x direction) for orbital mechanics.

    Physics: A body orbits under gravitational attraction from a central mass.
    The gravitational acceleration follows an inverse-square law:
    a = -GM/r^2 directed toward the central mass.

    For the x-component: dvx_dt = -GM * x / r^3
    where r = sqrt(x^2 + y^2)
    """
    GM = 0.9810385816

    results = []
    for point in input_data:
        x = point['x']
        y = point['y']

        # Calculate distance from central body
        r_squared = x * x + y * y
        r = math.sqrt(r_squared)

        # Calculate acceleration: a_x = -GM * x / r^3
        if r > 1e-10:  # Avoid division by zero
            r_cubed = r_squared * r
            dvx_dt = -GM * x / r_cubed
        else:
            dvx_dt = 0.0

        results.append({'dvx_dt': dvx_dt})

    return results
