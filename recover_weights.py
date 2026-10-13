"""Rebuild omitted binary model assets from the recorded fitting procedures."""

from __future__ import annotations

import pathlib
import pickle
import struct
from array import array

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler


BASE = pathlib.Path("outputs/bio_phys_30_gpt56sol_20260921/03_plots/LLM_vs_truth_20260922/gpt56sol_20260922_55x3")
PHYS017 = BASE / "physics_017/solutions"
PHYS018 = BASE / "physics_018/solutions/run_03_task__Tncebyi"
DATA017 = BASE / "physics_017/solutions/run_01_task__RAJrnU3/data/train_data.csv"
DATA018 = PHYS018 / "data/train_data.csv"


def features_017(data: pd.DataFrame) -> np.ndarray:
    l, energy, theta, dm2 = data.iloc[:, :4].to_numpy().T
    return np.c_[
        l / 100.0, energy / 50.0, theta, dm2,
        energy * theta / dm2, dm2 * l / energy,
        l * theta, l * theta / energy,
        energy * np.cos(2.0 * theta) / dm2,
        energy * np.sin(2.0 * theta) / dm2,
        np.sin(2.0 * theta), np.cos(2.0 * theta),
    ]


def physics017_run01() -> None:
    folder = PHYS017 / "run_01_task__RAJrnU3"
    data = pd.read_csv(DATA017)
    x = features_017(data)
    y = data.iloc[:, 4].to_numpy()
    scaler = StandardScaler().fit(x)
    z = scaler.transform(x)
    values = list(scaler.mean_) + list(scaler.scale_)
    models = []
    for seed in (1, 2):
        model = MLPRegressor(
            hidden_layer_sizes=(64, 64), activation="tanh", solver="adam",
            alpha=1e-5, batch_size=128, learning_rate_init=0.002,
            max_iter=3000, early_stopping=True, validation_fraction=0.15,
            n_iter_no_change=130, random_state=seed,
        ).fit(z, y)
        models.append(model)
    for model in models:
        for weights, biases in zip(model.coefs_, model.intercepts_):
            values.extend(weights.ravel(order="C"))
            values.extend(biases)
    payload = b"LAW1" + struct.pack("<I", len(models))
    payload += struct.pack(f"<{len(values)}f", *values)
    (folder / "law_weights.bin").write_bytes(payload)
    print("physics_017 run_01", len(payload), flush=True)


def physics017_run03() -> None:
    folder = PHYS017 / "run_03_task__tiaGM2W"
    data = pd.read_csv(DATA017)
    l, energy, theta, dm2 = data.iloc[:, :4].to_numpy().T
    features = np.c_[
        l, energy, theta, dm2, l / energy, dm2 * l / energy,
        1.0 / energy, 1.0 / theta, dm2 / energy,
        l / (energy * theta), dm2 * l / (energy * theta),
        np.log(l), np.log(energy), np.log(theta),
        np.sin(2.0 * theta), np.cos(theta),
    ]
    y = data.iloc[:, 4].to_numpy()
    scaler = StandardScaler().fit(features)
    z = scaler.transform(features)
    values = array("f", scaler.mean_.tolist() + scaler.scale_.tolist())
    for seed in range(3):
        model = MLPRegressor(
            hidden_layer_sizes=(100, 100, 50), activation="tanh", max_iter=300,
            early_stopping=False, random_state=seed, learning_rate_init=0.003,
            alpha=0.0001, tol=1e-9, n_iter_no_change=301,
        ).fit(z, y)
        for weights, biases in zip(model.coefs_, model.intercepts_):
            values.extend(weights.astype(np.float32).ravel().tolist())
            values.extend(biases.astype(np.float32).tolist())
    with (folder / "law_weights.raw").open("wb") as stream:
        values.tofile(stream)
    print("physics_017 run_03", (folder / "law_weights.raw").stat().st_size, flush=True)


def physics018_run03() -> None:
    data = pd.read_csv(DATA018)
    t, h, nd, strain = data.iloc[:, :4].to_numpy().T
    y = data.iloc[:, 4].to_numpy()
    control = 0.1 * (t - 300.0) + nd + 0.3 * np.tanh(strain / 0.003)
    features = np.c_[control, np.log(h), nd, strain * 100.0]
    scaler = StandardScaler().fit(features)
    z = scaler.transform(features)
    params = {"mean": scaler.mean_, "scale": scaler.scale_}
    for seed in (1, 7, 19):
        model = MLPRegressor(
            hidden_layer_sizes=(100, 100), activation="tanh", solver="adam",
            alpha=1e-6, max_iter=3000, random_state=seed,
            early_stopping=True, validation_fraction=0.12,
            n_iter_no_change=120, learning_rate_init=0.002,
        ).fit(z, y)
        for index, (weights, biases) in enumerate(zip(model.coefs_, model.intercepts_)):
            params[f"w{seed}_{index}"] = weights
            params[f"b{seed}_{index}"] = biases
    np.savez_compressed(PHYS018 / "law_weights.npz", **params)
    print("physics_018 run_03", (PHYS018 / "law_weights.npz").stat().st_size, flush=True)


if __name__ == "__main__":
    physics017_run01()
    physics017_run03()
    physics018_run03()
