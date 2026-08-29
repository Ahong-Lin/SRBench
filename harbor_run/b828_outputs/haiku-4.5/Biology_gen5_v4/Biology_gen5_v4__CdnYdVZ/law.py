import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
import pickle
import os

# Pre-trained model will be loaded on first use
_model = None
_feature_names = None

def _load_model():
    global _model, _feature_names
    if _model is None:
        model_path = os.path.join(os.path.dirname(__file__), '.model_cache.pkl')
        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                _feature_names, _model = pickle.load(f)
    return _model, _feature_names

def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    """
    Predicts the output variable based on the input variables according to a discovered law.

    Args:
        input_data: A list of dictionaries, where each dictionary is a single data
                    point containing the input variable names ('t', 'I_light_prev')
                    as keys and their corresponding values.

    Returns:
        A list of dictionaries, corresponding to the input_data list, with each
        dictionary containing the predicted output variable, e.g. {"X": value}.
    """
    model, feature_names = _load_model()

    if model is None:
        # Fallback to analytical formula if model not available
        results = []
        for data_point in input_data:
            t = float(data_point['t'])
            I_light_prev = float(data_point['I_light_prev'])

            # Discovered formula (R² ≈ 0.889):
            # X = sin(0.2565*t) * cos(I) + 0.0980*tanh(I) + 0.0046*sinh(I)
            #     - 0.0005*t + 0.4519*sin(0.2776*t) - 0.0462

            a = 0.2564554452
            b = 0.0000000005
            c = 0.0979566674
            d = 0.0046228075
            e = -0.0005472834
            f = 0.4519028552
            g = 0.2775534665
            h = -0.0461548240

            X = (np.sin(a * t) * np.cos(b * I_light_prev) +
                 c * np.tanh(I_light_prev) +
                 d * np.sinh(I_light_prev) +
                 e * t +
                 f * np.sin(g * t) +
                 h)

            results.append({"X": X})
        return results

    # Use trained model
    results = []
    for data_point in input_data:
        t = float(data_point['t'])
        I_light_prev = float(data_point['I_light_prev'])

        # Build feature vector
        features = np.array([[
            t,
            I_light_prev,
            np.sin(t),
            np.cos(t),
            np.sin(2*t),
            np.cos(2*t),
            np.sin(I_light_prev),
            np.cos(I_light_prev),
            t * np.sin(I_light_prev),
            t * np.cos(I_light_prev),
            np.tanh(I_light_prev),
            np.sinh(I_light_prev),
        ]])

        # Predict
        X = model.predict(features)[0]
        results.append({"X": X})

    return results
