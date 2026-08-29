def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dv_dt (acceleration) from observed variables using a
    full second-order polynomial regression model fitted to training data.

    The model uses: t, v, brake_temperature, cart_position and all their
    pairwise products and quadratic terms.
    """
    # Fitted coefficients from full second-order regression
    # Order: 1, t, t^2, v, v^2, brake_temp, brake_temp^2, cart_pos, cart_pos^2,
    #        t*v, t*brake_temp, t*cart_pos, v*brake_temp, v*cart_pos, brake_temp*cart_pos
    coeffs = [
        1.484435657749165e+02,
        6.113479655808243e+01,
        1.938008811835607e+00,
        -1.256697502237369e+01,
        2.535590638226462e-01,
        1.352823645995626e+01,
        1.207950873547742e-01,
        -1.268392062112241e+01,
        5.698437721489827e-02,
        -1.254203522063203e+00,
        1.827127808814772e+00,
        -6.935286429317510e-01,
        -3.318461127126708e-02,
        1.448894584449291e-01,
        -1.749336524517778e-01,
    ]

    results = []
    for row in input_data:
        t = row['t']
        v = row['v']
        brake_temperature = row['brake_temperature']
        cart_position = row['cart_position']

        # Compute all features for the second-order polynomial
        features = [
            1.0,                                    # intercept
            t,                                      # t
            t**2,                                   # t^2
            v,                                      # v
            v**2,                                   # v^2
            brake_temperature,                      # brake_temperature
            brake_temperature**2,                   # brake_temperature^2
            cart_position,                          # cart_position
            cart_position**2,                       # cart_position^2
            t * v,                                  # t*v
            t * brake_temperature,                  # t*brake_temperature
            t * cart_position,                      # t*cart_position
            v * brake_temperature,                  # v*brake_temperature
            v * cart_position,                      # v*cart_position
            brake_temperature * cart_position,      # brake_temperature*cart_position
        ]

        # Compute prediction as dot product
        dv_dt = sum(c * f for c, f in zip(coeffs, features))
        results.append({"dv_dt": dv_dt})

    return results
