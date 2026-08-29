def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dG_dt from glucose-insulin regulation dynamics.

    The discovered law is a linear combination with interaction term:
    dG/dt = -0.437095600743718*I + 0.099495410021054*G + 0.057546887903728*Ia - 0.029931198436924*I*G + 0.041343081579893

    Args:
        input_data: List containing exactly one dict with keys 't', 'G', 'I', 'Ia'

    Returns:
        List containing exactly one dict with key 'dG_dt' and the predicted value
    """
    # Coefficients from regression fit on training data
    a = -0.437095600743718  # coefficient of I (insulin)
    b = 0.099495410021054   # coefficient of G (glucose)
    c = 0.057546887903728   # coefficient of Ia (active insulin)
    d = -0.029931198436924  # coefficient of I*G interaction
    e = 0.041343081579893   # constant term

    row = input_data[0]
    G = row['G']
    I = row['I']
    Ia = row['Ia']

    # Evaluate the discovered law
    dG_dt = a * I + b * G + c * Ia + d * I * G + e

    return [{'dG_dt': dG_dt}]
