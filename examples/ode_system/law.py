"""Example approximation that treats the resource state as a constant."""
def law(rows):
    return [{"dN_dt": (0.8 * 5.0 / 6.0 - 0.2) * row["N"]} for row in rows]
