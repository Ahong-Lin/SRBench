def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dN/dt (cell growth rate) from observed variables.

    Discovered relationship:
    dN/dt = -105.81985715 + 0.13589622*N - 1.52059783*S - 0.61189813*A
            + 0.00000296*N*S + 0.00183273*N*A

    Where:
    - N: current cell count
    - S: surface area available (or resource indicator)
    - A: area parameter
    - t: time (not used in the model)
    """
    results = []

    # Coefficients from least-squares fit on training data
    c0 = -105.81985715
    c1 = 0.13589622
    c2 = -1.52059783
    c3 = -0.61189813
    c4 = 0.00000296
    c5 = 0.00183273

    for row in input_data:
        N = row['N']
        S = row['S']
        A = row['A']

        # Compute dN/dt using the discovered relationship
        dN_dt = c0 + c1*N + c2*S + c3*A + c4*N*S + c5*N*A

        results.append({'dN_dt': dN_dt})

    return results
