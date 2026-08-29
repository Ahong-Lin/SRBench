def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict the rate of change of daughter nuclide population (dNd_dt)
    in a two-level radioactive decay chain using a quadratic model.

    The discovered relationship is:
    dNd_dt = -0.135979705129*Np - 0.048700053204*Nd
             + 0.000020374183292*Np^2 + 0.000019258523589*Nd^2
             + 0.000025057514185*Np*Nd + 0.045777922877
    """
    c1 = -0.135979705128862
    c2 = -0.048700053203836
    c3 = 0.000020374183292
    c4 = 0.000019258523589
    c5 = 0.000025057514185
    c0 = 0.045777922876771

    results = []
    for row in input_data:
        Np = row['Np']
        Nd = row['Nd']

        dNd_dt = (c1 * Np + c2 * Nd +
                  c3 * Np**2 + c4 * Nd**2 +
                  c5 * Np * Nd + c0)

        results.append({'dNd_dt': dNd_dt})

    return results
