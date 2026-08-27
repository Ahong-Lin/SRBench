from sklearn.linear_model import LinearRegression
import numpy as np


def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dE_dt (rate of change of active enzyme concentration) from:
    - E: active enzyme concentration
    - A: aggregated/inactive enzyme concentration
    - G: temperature-dependent factor
    - t: time

    Uses a linear regression model fitted on the training data.
    """
    if not input_data:
        return []

    # Extract features in the correct order
    X = np.array([[point['E'], point['A'], point['G'], point['t']] for point in input_data])

    # Coefficients from fitted linear regression model
    # dE_dt = -0.240702*E + 0.369151*A + 0.028866*G + -0.022939*t + 0.423773
    coefficients = np.array([-0.2407024799, 0.3691513926, 0.0288657084, -0.0229390587])
    intercept = 0.4237730569

    # Compute predictions
    predictions = X @ coefficients + intercept

    # Return as list of dicts with dE_dt key
    return [{'dE_dt': float(pred)} for pred in predictions]
