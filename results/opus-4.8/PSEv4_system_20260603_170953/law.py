def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Predict dx_dt from observed inputs.

    The discovered relationship is dx/dt = v, i.e. the time derivative of the
    position x is exactly the velocity v. This is verified to hold with zero
    residual on the training data.
    """
    return [{"dx_dt": row["v"]} for row in input_data]
