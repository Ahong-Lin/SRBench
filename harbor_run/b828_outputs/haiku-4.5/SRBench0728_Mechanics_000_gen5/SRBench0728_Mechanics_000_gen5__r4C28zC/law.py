def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the instantaneous acceleration (dv_dt) of a braking system.

    The relationship is a cubic polynomial in v, brake_temperature, and cart_position.
    Discovered via symbolic regression on training data with R² = 0.9997.
    """
    results = []

    for row in input_data:
        v = row['v']
        brake_temp = row['brake_temperature']
        cart_pos = row['cart_position']

        # Cubic polynomial model
        # dv_dt = const + linear terms + quadratic terms + cubic terms + interactions
        dv_dt = (
            -6.0665522770
            + (-42.2371234373) * v
            + 49.5831160589 * brake_temp
            + 10.4157312106 * cart_pos
            + 4.2537313255 * (v ** 2)
            + (-1.2287765657) * (brake_temp ** 2)
            + (-0.0149334776) * (cart_pos ** 2)
            + (-0.1065377015) * (v ** 3)
            + 0.0125258744 * (brake_temp ** 3)
            + (-0.0000560509) * (cart_pos ** 3)
            + (-12.5193065124) * v * brake_temp
            + 3.7752681812 * v * cart_pos
            + (-0.4296391416) * brake_temp * cart_pos
            + 0.4511535752 * (v ** 2) * brake_temp
            + 0.1674972412 * v * (brake_temp ** 2)
            + (-0.1843254419) * (v ** 2) * cart_pos
            + (-0.0106484739) * v * (cart_pos ** 2)
            + 0.0007297772 * (brake_temp ** 2) * cart_pos
            + 0.0009974310 * brake_temp * (cart_pos ** 2)
            + (-0.0065760619) * (v ** 2) * (brake_temp ** 2)
            + 0.0026520985 * (v ** 2) * brake_temp * cart_pos
            + (-0.0006860419) * v * (brake_temp ** 2) * cart_pos
            + 0.0001397121 * v * brake_temp * (cart_pos ** 2)
        )

        results.append({"dv_dt": dv_dt})

    return results
