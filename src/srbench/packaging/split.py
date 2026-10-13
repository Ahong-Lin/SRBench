"""The explicit spatial/time holdout protocol; Sobol is only the sampler."""
import copy
import numpy as np
import pandas as pd
from srbench.generation.data_generator import gen_evaluate_explicit, gen_integrate_system, gen_root_solve_implicit
from .reference import truth_values


def _public_frame(frame, contract):
    columns = contract.features + [contract.target]
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"data is missing declared columns: {sorted(missing)}")
    out = frame.loc[:, columns].copy()
    values = out.to_numpy(dtype=float)
    if len(out) < 2 or not np.isfinite(values).all():
        raise ValueError("each partition needs at least two rows with finite numeric data")
    return out


def build_split(spec, contract, *, n_total=5000, test_points=500, seed=0, train_csv=None, test_csv=None):
    if (train_csv is None) != (test_csv is None):
        raise ValueError("provide both train_csv and test_csv, or neither")
    if train_csv is not None:
        train = _public_frame(pd.read_csv(train_csv), contract)
        test = _public_frame(pd.read_csv(test_csv), contract)
        manifest = {"protocol": "provided", "sampling": "existing CSV inputs; no resampling",
                    "space_fraction": None, "seed": None}
    else:
        if not 2 <= test_points <= n_total - 2:
            raise ValueError("need at least two training and two hidden test points")
        if not 0 <= seed < 2**32 - 1:
            raise ValueError("split seed must fit unsigned 32-bit seeds with room for seed+1")
        generator = gen_root_solve_implicit if contract.implicit_branch else gen_evaluate_explicit if contract.family == "static" else gen_integrate_system
        frames = []
        for partition, count, part_seed in [("train", n_total - test_points, seed), ("hidden", test_points, seed + 1)]:
            local = copy.deepcopy(spec)
            local.update(_n_total=count, _partition=partition)
            try:
                columns, values = generator(local, part_seed)
            except SystemExit as exc:
                raise ValueError(f"data generation failed: {exc}") from exc
            frame = pd.DataFrame(values, columns=columns)
            if len(frame) != count:
                raise ValueError("generator returned the wrong number of rows")
            clean = truth_values(contract, frame)
            if not np.allclose(clean, frame[contract.target], rtol=1e-9, atol=1e-11):
                raise ValueError("generated clean labels disagree with the packaged reference")
            frames.append(_public_frame(frame, contract))
        train, test = frames
        axes = spec["independent_variables"]
        one_axis = contract.family == "ode" or len(axes) == 1
        d = len(axes)
        cut = 0.9 if one_axis else 1.0 - 0.1 ** (1.0 / d)
        manifest = {
            "protocol": "time_right_extrapolation" if contract.family == "ode" else "right_interval" if one_axis else "upper_corner",
            "sampling": "grid in normalized coordinate" if one_axis else "scrambled Sobol, train rejects upper corner",
            "seed": seed, "test_seed": seed + 1,
            "train_space_fraction": 0.9, "test_space_fraction": 0.1,
            "normalized_boundary": cut,
            "test_region": "all normalized sampling coordinates > normalized_boundary",
            "coordinate_transform": {axis["symbol"]: axis.get("scale", "linear") for axis in axes},
            "sampling_ranges": {axis["symbol"]: axis["range"] for axis in axes},
            "ode_initialization": "integrate from original initial time and initial conditions for both partitions" if contract.family == "ode" else None,
            "data_origin": "regenerated from the same spec; not a split of candidate data.csv",
        }
    if train_csv is None and any(iv.get("type") == "integer" for iv in spec["independent_variables"]):
        from srbench.generation.data_generator import mixed_integer_geometry
        manifest.update(protocol="mixed_integer_upper_corner", normalized_boundary=None,
                        sampling="scrambled Sobol with uniform integer bins and joint-corner rejection",
                        test_region="all inputs strictly above their coordinate_boundaries",
                        coordinate_boundaries=mixed_integer_geometry(spec["independent_variables"]),
                        integer_inputs=[iv["symbol"] for iv in spec["independent_variables"] if iv.get("type") == "integer"],
                        space_measure="uniform counting measure on integer levels, normalized coordinate volume on continuous inputs")
    # Compare full declared feature tuples, not an individual marginal axis.
    train_keys = set(map(tuple, train[contract.features].to_numpy()))
    test_keys = set(map(tuple, test[contract.features].to_numpy()))
    if train_keys & test_keys:
        raise ValueError("training and hidden test feature tuples overlap")
    for frame in (train, test):
        if not np.allclose(truth_values(contract, frame), frame[contract.target], rtol=1e-9, atol=1e-11):
            raise ValueError("noise-free data does not match the specified ground truth")
    manifest.update(train_points=len(train), test_points=len(test),
                    label="clean_ground_truth", noise=0.0)
    return train, test, manifest
