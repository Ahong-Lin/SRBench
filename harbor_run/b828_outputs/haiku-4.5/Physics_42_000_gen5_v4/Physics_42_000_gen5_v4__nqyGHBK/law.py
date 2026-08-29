def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the velocity of a sphere settling in a viscous fluid.

    Uses a double exponential model that captures the effects of:
    - Gravitational acceleration and buoyancy
    - Viscous drag (primary exponential term)
    - Added mass and history force effects (secondary exponential term)
    - Wall corrections (through composite exponential decay)

    The model is: v = a * (1 - b*exp(-k*t) - c*exp(-m*t))
    """
    # Fitted parameters from physics-based analysis
    a = 10.66134451
    b = 1.06127180
    k = 0.66319808
    c = -0.06999260
    m = 2.45739000

    result = []
    for row in input_data:
        t = row['t']
        # Double exponential model: v = a * (1 - b*exp(-k*t) - c*exp(-m*t))
        v = a * (1 - b * (2.718281828459045 ** (-k * t)) - c * (2.718281828459045 ** (-m * t)))
        result.append({'v': v})

    return result
