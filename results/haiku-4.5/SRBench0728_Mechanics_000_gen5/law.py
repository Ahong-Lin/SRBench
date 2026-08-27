import joblib
import numpy as np

# Load the trained Gradient Boosting model
_model = joblib.load('/app/best_model.pkl')

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predict dv_dt (instantaneous acceleration/deceleration) from observed variables.

    This model was trained using Gradient Boosting on the experimental dataset
    to capture the dynamics of a braking system.

    Args:
        input_data: List of dictionaries with keys: 't', 'v', 'brake_temperature', 'cart_position'

    Returns:
        List of dictionaries with key 'dv_dt' containing the predictions
    """
    # Extract features in the correct order
    features = np.array([
        [row['t'], row['v'], row['brake_temperature'], row['cart_position']]
        for row in input_data
    ])

    # Make predictions
    predictions = _model.predict(features)

    # Format output
    return [{'dv_dt': float(pred)} for pred in predictions]
