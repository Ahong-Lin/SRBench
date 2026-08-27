def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """Predict dx_dt from inputs.

    Discovered relationship: dx/dt = v (exact identity).
    The velocity v is, by definition, the time derivative of position x.
    Verified on the training set with zero residual error.
    """
    return [{"dx_dt": row["v"]} for row in input_data]
