"""
Evaluation script for Biology_gen5 symbolic regression task.
Loads the agent's law.py, runs predictions on test data, computes R² score.
"""

import sys
import importlib.util
import numpy as np
import pandas as pd
from pathlib import Path

# ============ Configuration ============
LAW_PATH = Path("/app/law.py")
TEST_DATA_PATH = Path("/tests/test_data.csv")
REWARD_OUTPUT_FILE = Path("/logs/verifier/reward.txt")

# Task schema: define your feature columns and target column
FEATURE_NAMES = ["t", "I_light_prev"]       # TODO: 改成你的输入变量名
TARGET_NAME = "X"                            # TODO: 改成你的输出变量名


# ============ Metrics ============
def calculate_metrics(predictions, true_values):
    """Calculate NMSE, NMAE, and R² score."""
    predictions = np.array(predictions, dtype=float)
    true_values = np.array(true_values, dtype=float)

    # Check for invalid values
    if np.any(np.isnan(predictions)) or np.any(np.isinf(predictions)):
        print("[ERROR] Predictions contain NaN or Inf values.")
        return 100000.0, 100000.0, -1.0

    # NMSE = MSE / Var(y_true)
    mse = np.mean((predictions - true_values) ** 2)
    variance = np.var(true_values)
    if variance < 1e-12:
        print("[WARNING] Target variance is near zero.")
        nmse = 100000.0
    else:
        nmse = mse / variance

    # NMAE = MAE / MAD(y_true)
    mae = np.mean(np.abs(predictions - true_values))
    mad = np.mean(np.abs(true_values - np.mean(true_values)))
    if mad < 1e-12:
        nmae = 100000.0
    else:
        nmae = mae / mad

    # R² = 1 - NMSE
    r2 = 1.0 - nmse

    return nmse, nmae, r2


# ============ Main Evaluation ============
def main():
    # 1. Check law.py exists
    if not LAW_PATH.exists():
        print(f"[ERROR] {LAW_PATH} not found. Agent did not produce a solution.")
        write_reward(-1.0)
        sys.exit(1)

    # 2. Load agent's law function
    try:
        spec = importlib.util.spec_from_file_location("law_module", LAW_PATH)
        law_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(law_module)
        law_func = law_module.law
    except Exception as e:
        print(f"[ERROR] Failed to load law.py: {e}")
        write_reward(-1.0)
        sys.exit(1)

    # 3. Load test data
    try:
        df = pd.read_csv(TEST_DATA_PATH)
    except Exception as e:
        print(f"[ERROR] Failed to load test data: {e}")
        write_reward(-1.0)
        sys.exit(1)

    # 4. Prepare input and get predictions
    try:
        input_data = df[FEATURE_NAMES].to_dict(orient="records")
        true_values = df[TARGET_NAME].values.tolist()

        # Call the agent's law function
        # If your task has groups, loop over groups here (see Economy example)
        predictions_raw = law_func(input_data)

        # Extract predicted values
        if isinstance(predictions_raw, list) and len(predictions_raw) > 0:
            if isinstance(predictions_raw[0], dict):
                predictions = [p[TARGET_NAME] for p in predictions_raw]
            else:
                predictions = predictions_raw
        else:
            print(f"[ERROR] Invalid output format from law(). Expected list, got: {type(predictions_raw)}")
            write_reward(-1.0)
            sys.exit(1)

    except Exception as e:
        print(f"[ERROR] Error during prediction: {e}")
        write_reward(-1.0)
        sys.exit(1)

    # 5. Calculate metrics
    nmse, nmae, r2 = calculate_metrics(predictions, true_values)

    print(f"\n{'='*50}")
    print(f"Evaluation Results:")
    print(f"  NMSE: {nmse:.6f}")
    print(f"  NMAE: {nmae:.6f}")
    print(f"  R²:   {r2:.6f}")
    print(f"{'='*50}\n")

    # 6. Write reward
    write_reward(r2)


def write_reward(r2: float):
    """Write the R² score to the reward file."""
    REWARD_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REWARD_OUTPUT_FILE, "w") as f:
        f.write(f"{r2:.6f}\n")
    print(f"[INFO] Reward written to {REWARD_OUTPUT_FILE}: {r2:.6f}")


if __name__ == "__main__":
    main()
