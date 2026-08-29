def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Compute dvx_dt (rate of change of x-velocity) from observed system state.

    Fitted polynomial relationship discovered via regression analysis on 4500 training points.
    The underlying system appears to be a coupled nonlinear oscillator with quadratic damping.

    Formula: dvx_dt = c₀*x + c₁*y + c₂*vx + c₃*vy + c₄*x² + c₅*y² + c₆*vx² + c₇*vy²
                    + c₈*xy + c₉*xvx + c₁₀*xvy + c₁₁*yvx + c₁₂*yvy + c₁₃*vxvy + intercept
    """

    # Fitted coefficients (from 98.78% R² nonlinear regression on all 4500 training samples)
    # Trained on: x, y, vx, vy, x², y², vx², vy², xy, xvx, xvy, yvx, yvy, vxvy
    coefficients = {
        'x': 0.329908529,
        'y': 0.228008644,
        'vx': 0.535165552,
        'vy': -1.200534970,
        'x2': -0.210942237,
        'y2': -1.135778081,
        'vx2': -7.778630458,
        'vy2': -1.369906637,
        'xy': 0.646624534,
        'xvx': 1.986454605,
        'xvy': 1.049984889,
        'yvx': -5.957978657,
        'yvy': -0.754920879,
        'vxvy': -2.871410518,
        'intercept': 0.026774393,
    }

    results = []
    for row in input_data:
        x = row['x']
        y = row['y']
        vx = row['vx']
        vy = row['vy']

        # Compute dvx_dt using the fitted polynomial
        dvx_dt = (
            coefficients['x'] * x +
            coefficients['y'] * y +
            coefficients['vx'] * vx +
            coefficients['vy'] * vy +
            coefficients['x2'] * x * x +
            coefficients['y2'] * y * y +
            coefficients['vx2'] * vx * vx +
            coefficients['vy2'] * vy * vy +
            coefficients['xy'] * x * y +
            coefficients['xvx'] * x * vx +
            coefficients['xvy'] * x * vy +
            coefficients['yvx'] * y * vx +
            coefficients['yvy'] * y * vy +
            coefficients['vxvy'] * vx * vy +
            coefficients['intercept']
        )

        results.append({'dvx_dt': dvx_dt})

    return results
