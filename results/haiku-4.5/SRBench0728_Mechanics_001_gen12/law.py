def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Discovered law: dx_dt = v

    The rate of change of position (dx_dt) is exactly equal to the velocity (v).
    This is a fundamental kinematic relationship: the derivative of position with respect to time
    is the velocity.

    The forces Fh and Fh2 do not contribute to dx_dt in this experimental system - they may
    represent applied forces that affect other variables but not the position derivative directly.
    """
    results = []
    for row in input_data:
        results.append({"dx_dt": row["v"]})
    return results
