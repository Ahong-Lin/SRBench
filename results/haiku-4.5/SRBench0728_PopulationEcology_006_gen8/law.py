import pickle
import os

# Load the pre-trained Gradient Boosting model
model_path = os.path.join(os.path.dirname(__file__), 'gb_model.pkl')
with open(model_path, 'rb') as f:
    model = pickle.load(f)

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts dN_dt (population change rate) using a Gradient Boosting model
    trained on the experimental population dynamics dataset.

    Args:
        input_data: List of dictionaries with keys 't', 'N', and 'reproductive_adult_abundance'

    Returns:
        List of dictionaries with predicted 'dN_dt' values
    """
    import numpy as np

    # Extract features in the correct order
    features = []
    for item in input_data:
        features.append([
            item['t'],
            item['N'],
            item['reproductive_adult_abundance']
        ])

    X = np.array(features)
    predictions = model.predict(X)

    # Return results in the required format
    results = []
    for pred in predictions:
        results.append({'dN_dt': float(pred)})

    return results
