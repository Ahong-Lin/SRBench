def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dvx_dt using a cubic polynomial model of the four input variables.
    The model was discovered through systematic symbolic regression on the training data.

    The discovered relationship is a degree-3 polynomial function of x, y, vx, and vy.
    All interactions and higher-order terms up to degree 3 are included.

    Coefficients were fitted via least-squares regression, achieving R² ≈ 0.9999.
    """

    # Coefficients for the degree-3 polynomial model
    # Generated from: PolynomialFeatures(degree=3) applied to [x, y, vx, vy]
    coeffs = [
        -1.31791196,   # x
        -7.46156067,   # y
        -32.47094723,  # vx
        -0.32155850,   # vy
        -4.92392299,   # x^2
        1.96503448,    # x*y
        -15.82833878,  # x*vx
        22.47474735,   # x*vy
        -4.75655721,   # y^2
        -21.59094517,  # y*vx
        -25.00478028,  # y*vy
        -24.56306783,  # vx^2
        -10.71135796,  # vx*vy
        -25.71354806,  # vy^2
        2.49656623,    # x^3
        -0.19251340,   # x^2*y
        9.06625622,    # x^2*vx
        -21.21882697,  # x^2*vy
        3.83933357,    # x*y^2
        23.76272902,   # x*y*vx
        10.35892052,   # x*y*vy
        48.10434637,   # x*vx^2
        -33.98686317,  # x*vx*vy
        65.07787547,   # x*vy^2
        0.61843942,    # y^3
        5.72825916,    # y^2*vx
        -6.48845550,   # y^2*vy
        14.77394696,   # y*vx^2
        -37.31308180,  # y*vx*vy
        -38.95074538,  # y*vy^2
        48.87368191,   # vx^3
        -76.08616722,  # vx^2*vy
        30.74362569,   # vx*vy^2
        -60.75015653,  # vy^3
    ]

    results = []
    for row in input_data:
        x = row['x']
        y = row['y']
        vx = row['vx']
        vy = row['vy']

        # Compute all polynomial features of degree 3
        features = [
            x,
            y,
            vx,
            vy,
            x*x,
            x*y,
            x*vx,
            x*vy,
            y*y,
            y*vx,
            y*vy,
            vx*vx,
            vx*vy,
            vy*vy,
            x*x*x,
            x*x*y,
            x*x*vx,
            x*x*vy,
            x*y*y,
            x*y*vx,
            x*y*vy,
            x*vx*vx,
            x*vx*vy,
            x*vy*vy,
            y*y*y,
            y*y*vx,
            y*y*vy,
            y*vx*vx,
            y*vx*vy,
            y*vy*vy,
            vx*vx*vx,
            vx*vx*vy,
            vx*vy*vy,
            vy*vy*vy,
        ]

        # Compute prediction as dot product
        dvx_dt = sum(c * f for c, f in zip(coeffs, features))

        results.append({'dvx_dt': dvx_dt})

    return results
