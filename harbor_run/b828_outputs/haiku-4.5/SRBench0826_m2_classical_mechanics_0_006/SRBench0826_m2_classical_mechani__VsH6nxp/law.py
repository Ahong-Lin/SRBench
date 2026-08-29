import math

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dvx_dt for an orbiting body based on position and velocity.

    Discovered law:
    dvx_dt = -0.9704263228 * x/r³ - 0.1598423067 * y/r³
             - 0.0551627356 * x/r + 0.4327427350 * y/r + 0.0460046774

    where r = sqrt(x² + y²)

    This represents the x-component of the acceleration in a gravitational
    system with inverse-cube and inverse-linear correction terms.
    """

    # Coefficients discovered from training data
    coeff_x_r3 = -0.9704263228
    coeff_y_r3 = -0.1598423067
    coeff_x_r1 = -0.0551627356
    coeff_y_r1 = 0.4327427350
    const_term = 0.0460046774

    results = []
    for row in input_data:
        x = row['x']
        y = row['y']

        # Calculate distance from origin
        r_squared = x * x + y * y
        r = math.sqrt(r_squared)

        # Avoid division by zero (shouldn't happen in orbital mechanics)
        if r < 1e-10:
            dvx_dt = const_term
        else:
            r_cubed = r * r * r
            r_to_1 = r

            # Main gravitational term (inverse cube)
            term1 = coeff_x_r3 * x / r_cubed
            term2 = coeff_y_r3 * y / r_cubed

            # Correction terms (inverse linear)
            term3 = coeff_x_r1 * x / r_to_1
            term4 = coeff_y_r1 * y / r_to_1

            # Constant offset
            dvx_dt = term1 + term2 + term3 + term4 + const_term

        results.append({'dvx_dt': dvx_dt})

    return results
