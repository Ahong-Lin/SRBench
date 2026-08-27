def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dG_dt (rate of change of plasma glucose) using the fitted mathematical law.

    Model: dG_dt = a + b*G + c*I + d*I² + e*Ia + f*I*Ia + h*Ia²

    Args:
        input_data: list of dicts with keys 't', 'G', 'I', 'Ia' (observed plasma variables)

    Returns:
        list of dicts with 'dG_dt' predictions
    """
    # Fitted parameters from symbolic regression
    a = 0.38885373188704664
    b = 0.01585555451701768
    c = -0.227691036206668
    d = -0.0473643676501192
    e = -0.29903133396143455
    f = -0.03714866917997629
    h = 0.08093487203666755

    results = []
    for sample in input_data:
        G = sample['G']
        I = sample['I']
        Ia = sample['Ia']

        # Linear combination with quadratic and interaction terms
        dG_dt = a + b*G + c*I + d*(I**2) + e*Ia + f*(I*Ia) + h*(Ia**2)

        results.append({'dG_dt': dG_dt})

    return results
