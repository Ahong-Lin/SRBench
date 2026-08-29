import numpy as np

# Precomputed coefficients from polynomial regression on training data
# Model: polynomial of degree 3 with all cross-terms up to degree 3
# Features: [1, N, crowding_load, t, N^2, crowding_load^2, t^2,
#           N*crowding_load, N*t, crowding_load*t,
#           N^3, crowding_load^3, t^3,
#           N^2*crowding_load, N^2*t, N*crowding_load^2, N*crowding_load*t, N*t^2,
#           crowding_load^2*t, crowding_load*t^2]

COEFFICIENTS = np.array([
    -2.858265252615197e+01,
    2.877767742098739e+00,
    -2.103011304044534e+00,
    -1.409450605165382e+02,
    -2.377740365135963e-03,
    1.263565540825900e-03,
    9.855671420823764e-01,
    1.381079416401364e-03,
    -3.274963230069075e-05,
    2.426756493129765e-01,
    8.283511831264649e-07,
    -8.905813245583111e-07,
    -5.071408021111298e-03,
    -9.126195769122302e-07,
    -6.215688878636314e-05,
    4.580572903793579e-07,
    7.297160570020470e-05,
    6.606989186579437e-04,
    -1.448227988249828e-04,
    -1.008602670556153e-03,
])


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dN_dt from input variables using a polynomial regression model.

    The model is: dN_dt = f(t, N, crowding_load)
    where f is a cubic polynomial with cross-terms, fitted to training data.

    Args:
        input_data: List of dictionaries with keys 't', 'N', 'crowding_load'

    Returns:
        List of dictionaries with key 'dN_dt' containing predictions
    """
    results = []

    for row in input_data:
        t = row['t']
        N = row['N']
        crowding_load = row['crowding_load']

        # Build feature vector for this sample
        features = np.array([
            1.0,                    # constant
            N,                      # N
            crowding_load,          # crowding_load
            t,                      # t
            N**2,                   # N^2
            crowding_load**2,       # crowding_load^2
            t**2,                   # t^2
            N * crowding_load,      # N*crowding_load
            N * t,                  # N*t
            crowding_load * t,      # crowding_load*t
            N**3,                   # N^3
            crowding_load**3,       # crowding_load^3
            t**3,                   # t^3
            N**2 * crowding_load,   # N^2*crowding_load
            N**2 * t,               # N^2*t
            N * crowding_load**2,   # N*crowding_load^2
            N * crowding_load * t,  # N*crowding_load*t
            N * t**2,               # N*t^2
            crowding_load**2 * t,   # crowding_load^2*t
            crowding_load * t**2,   # crowding_load*t^2
        ])

        # Compute prediction
        dN_dt = float(np.dot(features, COEFFICIENTS))

        results.append({"dN_dt": dN_dt})

    return results
