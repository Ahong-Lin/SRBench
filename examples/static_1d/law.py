"""Deliberately simplified fit, for demonstrating extrapolation error."""
def law(rows):
    return [{"F": -1.0 * row["x"]} for row in rows]
