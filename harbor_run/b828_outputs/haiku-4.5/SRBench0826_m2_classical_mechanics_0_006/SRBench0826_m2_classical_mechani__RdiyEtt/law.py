def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dvx_dt from orbital dynamics data.

    The discovered relationship is a generalized orbital dynamics law that combines:
    - Gravitational acceleration (inverse-square law with correction)
    - Velocity coupling terms (Coriolis-like interactions)

    Formula:
    dvx_dt = c_x_r3 * x / r³
           + c_y_r3 * y / r³
           + c_x_r5 * x / r⁵
           + c_y_r5 * y / r⁵
           + c_vx * vx
           + c_vy * vy
           + c_xvy * x * vy
           + c_yvx * y * vx

    where r = sqrt(x² + y²)
    """

    # Fitted coefficients
    c_x_r3  = 1.5548773412416084
    c_y_r3  = 0.579059594021416
    c_x_r5  = -0.3304207038790345
    c_y_r5  = -0.08904826673608043
    c_vx    = 0.7836782282949732
    c_vy    = -3.1273306653015784
    c_xvy   = 0.20527702436162656
    c_yvx   = 1.6862223608469595

    result = []
    for row in input_data:
        x = row['x']
        y = row['y']
        vx = row['vx']
        vy = row['vy']

        # Calculate distance
        r_squared = x * x + y * y
        r = r_squared ** 0.5

        # Handle edge case
        if r == 0:
            r = 1e-10

        r_cubed = r ** 3
        r_to_5 = r ** 5

        # Apply the discovered law
        dvx_dt = (
            c_x_r3 * x / r_cubed
            + c_y_r3 * y / r_cubed
            + c_x_r5 * x / r_to_5
            + c_y_r5 * y / r_to_5
            + c_vx * vx
            + c_vy * vy
            + c_xvy * x * vy
            + c_yvx * y * vx
        )

        result.append({'dvx_dt': dvx_dt})

    return result
