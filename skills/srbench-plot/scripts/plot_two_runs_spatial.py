"""Create a 0920-style 2x4 spatial comparison for two cached runs."""
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


def _read(path: Path, features: list[str]) -> pd.DataFrame:
    frame = pd.read_csv(path)
    required = set(features + ["ground_truth", "prediction", "partition"])
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")
    return frame


def _transform(frame: pd.DataFrame, features: list[str], log_features: set[str]) -> tuple[np.ndarray, list[str]]:
    raw = frame[features].to_numpy(dtype=float).copy()
    labels = list(features)
    for index, name in enumerate(features):
        if name in log_features:
            if np.any(raw[:, index] <= 0):
                raise ValueError(f"log feature {name!r} contains non-positive values")
            raw[:, index] = np.log10(raw[:, index])
            labels[index] = f"log10({name})"
    return raw, labels


def _plot_run(fig, frame: pd.DataFrame, features: list[str], log_features: set[str],
              offset: int, run_label: str) -> dict:
    coordinates, labels = _transform(frame, features, log_features)
    truth = frame["ground_truth"].to_numpy(dtype=float)
    prediction = frame["prediction"].to_numpy(dtype=float)
    test = frame["partition"].to_numpy(dtype=str) == "test"
    lower = float(np.nanmin(np.concatenate([truth, prediction])))
    upper = float(np.nanmax(np.concatenate([truth, prediction])))
    span = max(upper - lower, 1e-12)
    norm = Normalize(lower, upper if upper > lower else lower + 1)
    floor = lower - .08 * span
    hull = None
    if test.sum() >= 3:
        try:
            hull = coordinates[test][ConvexHull(coordinates[test]).vertices]
        except QhullError:
            pass
    triangulation = mtri.Triangulation(coordinates[:, 0], coordinates[:, 1])
    mixed = np.ptp(test[triangulation.triangles].astype(int), axis=1) != 0
    triangulation.set_mask(mixed)
    axes = []
    # Top pair: sampled values. Bottom pair: triangulated response surfaces.
    for values, name in ((truth, "Ground truth"), (prediction, "LLM solution")):
        ax = fig.add_subplot(2, 4, offset + len(axes) + 1)
        axes.append(ax)
        scatter = ax.scatter(coordinates[:, 0], coordinates[:, 1], c=values,
                             norm=norm, cmap="viridis", s=9, alpha=.78,
                             linewidths=0, rasterized=True)
        if hull is not None:
            closed = np.vstack([hull, hull[0]])
            ax.plot(closed[:, 0], closed[:, 1], color=PINK, lw=2, ls="--")
        ax.set(xlabel=labels[0], ylabel=labels[1], title=f"{run_label} | {name}\nsampled values")
        ax.grid(alpha=.12)
    for values, name, color in ((truth, "Ground truth", TRUTH),
                                (prediction, "LLM solution", PREDICTION)):
        ax = fig.add_subplot(2, 4, offset + len(axes) + 1, projection="3d")
        axes.append(ax)
        try:
            ax.plot_trisurf(triangulation, values, color=color, alpha=.86,
                            linewidth=0, antialiased=True)
        except (ValueError, RuntimeError, QhullError):
            ax.scatter(coordinates[:, 0], coordinates[:, 1], values,
                       c=values, cmap="viridis", norm=norm, s=7, alpha=.7,
                       rasterized=True)
        if hull is not None:
            polygon = np.column_stack([hull, np.full(len(hull), floor)])
            ax.add_collection3d(Poly3DCollection([polygon], facecolor=PINK_FILL,
                                                 edgecolor=PINK, alpha=.84))
        ax.set(xlabel=labels[0], ylabel=labels[1], zlabel="target",
               title=f"{run_label} | {name}\nsurface from samples")
        ax.set_zlim(floor, upper + .05 * span)
        ax.view_init(elev=28, azim=-125)
        ax.grid(alpha=.12)
    if hull is not None:
        axes[0].legend(handles=[Line2D([0], [0], color=PINK, ls="--", lw=2,
                                       label="held-out sample hull")],
                       frameon=False, fontsize=8, loc="best")
    fig.colorbar(scatter, ax=axes[:2], shrink=.82, label="target value")
    return {"run": run_label, "n": int(len(frame)), "train": int((~test).sum()),
            "test": int(test.sum()), "value_min": lower, "value_max": upper,
            "coordinate_labels": labels}


def plot(paths: list[Path], features: list[str], output: Path,
         labels: list[str], title: str, log_features: set[str]) -> dict:
    if len(paths) != 2:
        raise ValueError("exactly two --predictions files are required")
    if len(features) != 2:
        raise ValueError("two-run spatial figures require exactly two features")
    frames = [_read(path, features) for path in paths]
    fig = plt.figure(figsize=(22, 9), constrained_layout=True)
    runs = [_plot_run(fig, frame, features, log_features, offset, label)
            for offset, (frame, label) in zip((0, 4), zip(frames, labels))]
    fig.suptitle(title + "\nEach run has its own truth/prediction scale; pink = held-out region",
                 fontsize=14)
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "two_runs_spatial.png", dpi=175, bbox_inches="tight")
    fig.savefig(output / "two_runs_spatial.pdf", bbox_inches="tight")
    # Keep the conventional names for gallery consumers.
    fig.savefig(output / "spatial.png", dpi=175, bbox_inches="tight")
    fig.savefig(output / "spatial.pdf", bbox_inches="tight")
    plt.close(fig)
    metadata = {"features": features, "runs": runs,
                "residual_plotted": False,
                "meaning": "two independent 0920-style spatial views; surfaces use cached samples",
                "log_features": sorted(log_features),
                "files": [str(path) for path in paths]}
    (output / "two_runs_spatial_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, nargs=2, type=Path)
    parser.add_argument("--features", required=True, nargs=2)
    parser.add_argument("--labels", nargs=2, default=["run_01", "run_02"])
    parser.add_argument("--log-features", nargs="*", default=[])
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title", default="SRBench two-run spatial comparison")
    args = parser.parse_args()
    metadata = plot(args.predictions, args.features, args.output, args.labels,
                    args.title, set(args.log_features))
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
