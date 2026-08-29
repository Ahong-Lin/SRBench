def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict instantaneous acceleration (dv/dt) using a degree-2 polynomial model
    fitted to the training dataset.

    The model captures the relationship between velocity change rate and:
    - time (t)
    - velocity (v)
    - brake temperature
    - cart position

    Returns a list with one prediction dictionary per input row.
    """
    results = []

    # Fitted coefficients for degree-2 polynomial
    intercept = 14.5932590852
    c_t = 0.0559156377
    c_v = 0.0561308208
    c_brake = -0.3608997182
    c_cart = -0.5493250102
    c_t2 = 0.9052508964
    c_tv = 1.8631778091
    c_t_brake = 0.3961718507
    c_t_cart = -0.2377232863
    c_v2 = -0.0438495359
    c_v_brake = 0.2635377441
    c_v_cart = -0.2195334693
    c_brake2 = 0.0383147052
    c_brake_cart = -0.0415195064
    c_cart2 = 0.0154674341

    for row in input_data:
        t = row['t']
        v = row['v']
        brake_temperature = row['brake_temperature']
        cart_position = row['cart_position']

        # Compute degree-2 polynomial
        dv_dt = (
            intercept
            + c_t * t
            + c_v * v
            + c_brake * brake_temperature
            + c_cart * cart_position
            + c_t2 * (t ** 2)
            + c_tv * t * v
            + c_t_brake * t * brake_temperature
            + c_t_cart * t * cart_position
            + c_v2 * (v ** 2)
            + c_v_brake * v * brake_temperature
            + c_v_cart * v * cart_position
            + c_brake2 * (brake_temperature ** 2)
            + c_brake_cart * brake_temperature * cart_position
            + c_cart2 * (cart_position ** 2)
        )

        results.append({"dv_dt": dv_dt})

    return results
