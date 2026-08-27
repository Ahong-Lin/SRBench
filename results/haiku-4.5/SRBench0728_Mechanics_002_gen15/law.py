import numpy as np

# Pre-trained model coefficients (degree 2 polynomial)
# Feature order: vy, x, y, vx, vy^2, vy*x, vy*y, vy*vx, x^2, x*y, x*vx, y^2, y*vx, vx^2
_model_coef = np.array([
    -1.2005349702711634,   # vy
     0.32990852938155657,   # x
     0.228008644048523,    # y
     0.5351655518018973,   # vx
    -1.369906636770975,    # vy^2
     1.0499848890707066,   # vy*x
    -0.7549208794839977,   # vy*y
    -2.8714105182230614,   # vy*vx
    -0.21094223672526602,  # x^2
     0.6466245338750078,   # x*y
     1.9864546047523177,   # x*vx
    -1.1357780806489108,   # y^2
    -5.957978656578414,    # y*vx
    -7.778630457881998,    # vx^2
])
_model_intercept = 0.026774393240124976


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dvx_dt using a degree-2 polynomial regression model.

    The model is trained on the relationship between:
    - Inputs: vy (y-velocity), x, y (position), vx (x-velocity)
    - Output: dvx_dt (acceleration in x-direction)

    The formula uses polynomial features up to degree 2:
    [vy, x, y, vx, vy^2, vy*x, vy*y, vy*vx, x^2, x*y, x*vx, y^2, y*vx, vx^2]
    """
    results = []

    for row in input_data:
        vy = row['vy']
        x = row['x']
        y = row['y']
        vx = row['vx']

        # Create polynomial features manually to match sklearn's PolynomialFeatures
        # Order: [vy, x, y, vx, vy^2, vy*x, vy*y, vy*vx, x^2, x*y, x*vx, y^2, y*vx, vx^2]
        poly_features = np.array([
            vy,
            x,
            y,
            vx,
            vy * vy,
            vy * x,
            vy * y,
            vy * vx,
            x * x,
            x * y,
            x * vx,
            y * y,
            y * vx,
            vx * vx,
        ])

        # Compute prediction
        dvx_dt_pred = np.dot(poly_features, _model_coef) + _model_intercept

        results.append({'dvx_dt': float(dvx_dt_pred)})

    return results
