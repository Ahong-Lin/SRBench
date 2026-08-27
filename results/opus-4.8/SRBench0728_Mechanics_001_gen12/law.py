def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    # Kinematic identity: dx/dt = v (velocity). Holds exactly in the training data.
    return [{"dx_dt": row["v"]} for row in input_data]
