"""Example approximation that omits resource and temperature effects."""
def law(rows):
    return [{"growth": 0.55 * row["N"] * (1 - row["N"] / 120.0)} for row in rows]
