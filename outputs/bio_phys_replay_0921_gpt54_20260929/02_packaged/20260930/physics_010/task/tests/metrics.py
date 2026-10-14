"""Unclipped regression metrics shared by local plots and Harbor verification."""
import numpy as np


def regression_metrics(predictions, truth):
    predictions = np.asarray(predictions, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if predictions.ndim != 1 or predictions.shape != truth.shape or not len(truth):
        raise ValueError("metrics require equally sized, nonempty prediction and truth vectors")
    if not np.isfinite(predictions).all() or not np.isfinite(truth).all():
        raise ValueError("metrics cannot discard NaN/Inf predictions or labels")
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        delta = predictions - truth
        mse = float(np.mean(delta ** 2))
        mae = float(np.mean(np.abs(delta)))
        variance = float(np.var(truth))
        mad = float(np.mean(np.abs(truth - np.mean(truth))))
        scale = float(np.max(np.abs(truth)))
        scaled_truth = truth / scale if scale else truth
        scaled_variance = float(np.var(scaled_truth))
        scaled_mad = float(np.mean(np.abs(scaled_truth - np.mean(scaled_truth))))
        defined = len(truth) >= 2 and scaled_variance > (64 * np.finfo(float).eps)**2 and scaled_mad > 64 * np.finfo(float).eps
        scaled_delta = delta / scale if scale else delta
        nmse = float(np.mean(scaled_delta**2)) / scaled_variance if defined else None
        nmae = float(np.mean(np.abs(scaled_delta))) / scaled_mad if defined else None
        return {"n": len(truth), "rmse": float(np.sqrt(mse)), "mae": mae,
            "target_variance": variance, "raw_r2": 1.0 - nmse if defined else None,
            "nmse": nmse, "nmae": nmae,
            "status": "ok" if defined else "undefined_target_variance"}
