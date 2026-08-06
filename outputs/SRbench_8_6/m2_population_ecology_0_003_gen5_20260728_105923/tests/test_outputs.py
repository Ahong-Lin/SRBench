"""
Evaluation script for m2_population_ecology_0_003_gen5_20260728_105923 symbolic regression task.
Loads the agent's law.py, runs predictions on test data, and computes an R2 score.
"""

import sys
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd


LAW_PATH = Path("/app/law.py")
TEST_DATA_PATH = Path("/tests/test_data.csv")
REWARD_OUTPUT_FILE = Path("/logs/verifier/reward.txt")

FEATURE_NAMES = ['t', 'N1', 'N2', 'R']
TARGET_NAME = 'dN1_dt'


def calculate_metrics(predictions, true_values):
    predictions = np.array(predictions, dtype=float)
    true_values = np.array(true_values, dtype=float)

    if predictions.shape != true_values.shape:
        print(f"[ERROR] Prediction length mismatch: got {predictions.shape}, expected {true_values.shape}.")
        return 100000.0, 100000.0, -1.0

    if np.any(np.isnan(predictions)) or np.any(np.isinf(predictions)):
        print("[ERROR] Predictions contain NaN or Inf values.")
        return 100000.0, 100000.0, -1.0

    mse = np.mean((predictions - true_values) ** 2)
    variance = np.var(true_values)
    nmse = 100000.0 if variance < 1e-12 else mse / variance

    mae = np.mean(np.abs(predictions - true_values))
    mad = np.mean(np.abs(true_values - np.mean(true_values)))
    nmae = 100000.0 if mad < 1e-12 else mae / mad

    r2 = 1.0 - nmse
    return nmse, nmae, r2


def main():
    if not LAW_PATH.exists():
        print(f"[ERROR] {LAW_PATH} not found. Agent did not produce a solution.")
        write_reward(-1.0)
        sys.exit(1)

    try:
        spec = importlib.util.spec_from_file_location("law_module", LAW_PATH)
        law_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(law_module)
        law_func = law_module.law
    except Exception as e:
        print(f"[ERROR] Failed to load law.py: {e}")
        write_reward(-1.0)
        sys.exit(1)

    try:
        df = pd.read_csv(TEST_DATA_PATH)
    except Exception as e:
        print(f"[ERROR] Failed to load test data: {e}")
        write_reward(-1.0)
        sys.exit(1)

    try:
        input_data = df[FEATURE_NAMES].to_dict(orient="records")
        true_values = df[TARGET_NAME].values.tolist()
        predictions_raw = law_func(input_data)

        if isinstance(predictions_raw, list) and len(predictions_raw) == len(true_values):
            if len(predictions_raw) > 0 and isinstance(predictions_raw[0], dict):
                predictions = [p[TARGET_NAME] for p in predictions_raw]
            else:
                predictions = predictions_raw
        else:
            print(f"[ERROR] Invalid output format from law(). Expected list of length {len(true_values)}, got: {type(predictions_raw)}")
            write_reward(-1.0)
            sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Error during prediction: {e}")
        write_reward(-1.0)
        sys.exit(1)

    nmse, nmae, r2 = calculate_metrics(predictions, true_values)

    print(f"\n{'=' * 50}")
    print("Evaluation Results:")
    print(f"  NMSE: {nmse:.6f}")
    print(f"  NMAE: {nmae:.6f}")
    print(f"  R2:   {r2:.6f}")
    print(f"{'=' * 50}\n")

    write_reward(r2)


def write_reward(r2: float):
    REWARD_OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(REWARD_OUTPUT_FILE, "w") as f:
        f.write(f"{r2:.6f}\n")
    print(f"[INFO] Reward written to {REWARD_OUTPUT_FILE}: {r2:.6f}")


if __name__ == "__main__":
    main()
