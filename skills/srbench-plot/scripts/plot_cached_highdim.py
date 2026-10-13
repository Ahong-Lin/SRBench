"""Plot conditional surfaces for cached static SRBench predictions.

The helper never calls a submitted law and never changes scores. For a static
function with three or more inputs, the first two inputs are displayed as the
surface coordinates. The remaining inputs are fixed by selecting a nearby
band of already sampled rows. The output is a conditional-band surface, not a
claim to show the complete high-dimensional function.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from scipy.spatial import ConvexHull, QhullError


PINK = "#f098b4"
PINK_FILL = "#fce4ec"
TRUTH = "#2563a6"
PREDICTION = "#d05d27"


def _norm(values: np.ndarray) -> Normalize:
    finite = np.asarray(values, dtype=float)
    finite = finite[np.isfinite(finite)]
    if finite.size == 0:
        return Normalize(0.0, 1.0)
    low, high = float(finite.min()), float(finite.max())
    if high <= low:
        delta = max(abs(low) * 1e-6, 1e-9)
        return Normalize(low - delta, high + delta)
    return Normalize(low, high)


def _coordinates(frame: pd.DataFrame, features: list[str]) -> tuple[np.ndarray, list[float], list[float]]:
    raw = frame[features].to_numpy(dtype=float)
    low = np.nanmin(raw, axis=0)
    high = np.nanmax(raw, axis=0)
    span = high - low
    span[span == 0] = 1.0
    return (raw - low) / span, low.tolist(), high.tolist()


def _conditions(dimension: int) -> list[tuple[float, ...]]:
    """Return interpretable normalized conditioning locations."""
    if dimension == 3:
        return [(0.2,), (0.5,), (0.8,)]
    # For four or more inputs, show low/high combinations of the first two
    # conditioning coordinates. Remaining coordinates stay near 0.5.
    return [(a, b) for a in (0.2, 0.8) for b in (0.2, 0.8)]


def _condition_label(features: list[str], condition: tuple[float, ...]) -> str:
    shown = features[2:2 + len(condition)]
    return ", ".join(f"{name}≈{value:.1f}" for name, value in zip(shown, condition))


def _select_band(coordinates: np.ndarray, conditioning: np.ndarray,
                 condition: tuple[float, ...], target_points: int) -> np.ndarray:
    """Select nearest existing rows rather than inventing a new grid."""
    if conditioning.shape[1] == 1:
        distance = np.abs(conditioning[:, 0] - condition[0])
    else:
        target = np.asarray(condition, dtype=float)
        distance = np.linalg.norm(conditioning - target[None, :], axis=1)
    finite = np.isfinite(distance) & np.isfinite(coordinates).all(axis=1)
    candidates = np.flatnonzero(finite)
    if candidates.size <= target_points:
        return candidates
    order = candidates[np.argsort(distance[candidates], kind="stable")]
    return order[:target_points]


def _surface(ax, xy: np.ndarray, values: np.ndarray, partition: np.ndarray,
             value_norm: Normalize, title: str, labels: tuple[str, str],
             color: str, z_limits: tuple[float, float]) -> bool:
    floor = z_limits[0]
    finite = np.isfinite(xy).all(axis=1) & np.isfinite(values)
    if finite.sum() < 3 or np.unique(xy[finite], axis=0).shape[0] < 3:
        ax.set_title(title + " (insufficient non-collinear samples)")
        return False
    xy = xy[finite]
    values = values[finite]
    partition = partition[finite]
    try:
        triangulation = mtri.Triangulation(xy[:, 0], xy[:, 1])
        mixed = np.ptp((partition == "test")[triangulation.triangles].astype(int), axis=1) != 0
        triangulation.set_mask(mixed)
        ax.plot_trisurf(triangulation, values, color=color, alpha=.86,
                        linewidth=0, antialiased=True)
    except (ValueError, RuntimeError, QhullError):
        ax.scatter(xy[:, 0], xy[:, 1], values, c=values, cmap="viridis",
                   norm=value_norm, s=7, alpha=.7, rasterized=True)

    test = partition == "test"
    if test.any():
        # A pink floor marker/hull identifies the held-out part without
        # pretending that the test values were available to the model.
        ax.scatter(xy[test, 0], xy[test, 1], np.full(test.sum(), floor),
                   facecolors=PINK_FILL, edgecolors=PINK, linewidths=.45,
                   s=17, alpha=.9, rasterized=True)
        if test.sum() >= 3:
            try:
                hull = ConvexHull(xy[test])
                points = xy[test][hull.vertices]
                polygon = np.column_stack([points, np.full(len(points), floor)])
                ax.add_collection3d(Poly3DCollection([polygon], facecolor=PINK_FILL,
                                                     edgecolor=PINK, alpha=.42))
            except QhullError:
                pass
    ax.set(xlabel=labels[0], ylabel=labels[1], zlabel="target",
           title=title, xlim=(0, 1), ylim=(0, 1), zlim=z_limits)
    ax.view_init(elev=28, azim=-125)
    ax.grid(alpha=.16)
    return True


def plot(frame: pd.DataFrame, features: list[str], output: Path, title: str,
         band_points: int = 700) -> dict:
    if len(features) < 3:
        raise ValueError("This helper is for three or more independent inputs")
    required = set(features + ["ground_truth", "prediction", "partition"])
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"predictions.csv is missing columns: {sorted(missing)}")
    coordinates, low, high = _coordinates(frame, features)
    truth = frame["ground_truth"].to_numpy(dtype=float)
    prediction = frame["prediction"].to_numpy(dtype=float)
    partition = frame["partition"].to_numpy(dtype=str)
    finite = np.isfinite(coordinates).all(axis=1) & np.isfinite(truth) & np.isfinite(prediction)
    if finite.sum() < 3:
        raise ValueError("predictions.csv has fewer than three finite rows")
    value_norm = _norm(np.concatenate([truth[finite], prediction[finite]]))
    lower = float(value_norm.vmin)
    upper = float(value_norm.vmax)
    span = max(upper - lower, 1e-12)
    floor = lower - .10 * span
    z_limits = (floor, upper + .05 * span)
    conditioning = coordinates[:, 2:]
    conditions = _conditions(len(features))
    ncols = len(conditions)
    fig = plt.figure(figsize=(5.5 * ncols, 9.0), constrained_layout=True)
    grid = fig.add_gridspec(2, ncols)
    labels = (f"norm({features[0]})", f"norm({features[1]})")
    metadata_conditions = []
    for col, condition in enumerate(conditions):
        nearest = _select_band(coordinates, conditioning, condition, band_points)
        mask = np.zeros(len(frame), dtype=bool)
        mask[nearest] = True
        mask &= finite
        indices = np.flatnonzero(mask)
        label = _condition_label(features, condition)
        metadata_conditions.append({"normalized_values": list(condition),
                                    "label": label,
                                    "rows": int(indices.size)})
        selected_xy = coordinates[indices, :2]
        selected_partition = partition[indices]
        ax = fig.add_subplot(grid[0, col], projection="3d")
        _surface(ax, selected_xy, truth[indices], selected_partition, value_norm,
                 f"Ground truth | {label}", labels, TRUTH, z_limits)
        ax = fig.add_subplot(grid[1, col], projection="3d")
        _surface(ax, selected_xy, prediction[indices], selected_partition, value_norm,
                 f"LLM solution | {label}", labels, PREDICTION, z_limits)
    fig.colorbar(plt.cm.ScalarMappable(norm=value_norm, cmap="viridis"),
                 ax=list(fig.axes), shrink=.78, label="target value")
    fig.suptitle(title + "\nConditional-band surfaces from existing samples; pink floor = held-out samples",
                 fontsize=13)
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "conditional_slices.png", dpi=170, bbox_inches="tight")
    fig.savefig(output / "conditional_slices.pdf", bbox_inches="tight")
    # Keep the old filename so existing gallery links remain valid.
    fig.savefig(output / "highdim.png", dpi=170, bbox_inches="tight")
    fig.savefig(output / "highdim.pdf", bbox_inches="tight")
    plt.close(fig)
    metadata = {
        "input_dimension": len(features),
        "features": features,
        "displayed_features": features[:2],
        "conditioning_features": features[2:],
        "conditioning_slices": metadata_conditions,
        "conditioning_method": "nearest existing rows in normalized conditioning space",
        "band_points_target": band_points,
        "normalization_min": low,
        "normalization_max": high,
        "residual_plotted": False,
        "plots": ["conditional_slices", "highdim"],
        "meaning": "conditional-band surfaces; not a complete d-dimensional surface",
    }
    (output / "highdim_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--features", required=True, nargs="+")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title", default="SRBench conditional-surface comparison")
    parser.add_argument("--band-points", type=int, default=700)
    args = parser.parse_args()
    frame = pd.read_csv(args.predictions)
    metadata = plot(frame, args.features, args.output, args.title, args.band_points)
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
