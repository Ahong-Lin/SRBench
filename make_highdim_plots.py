"""Create honest high-dimensional comparison plots for static SRBench tasks.

The standard comparison figure is intentionally one-dimensional for static
multi-input data (it uses sample rank).  This script adds conditional visual
summaries for three- and four-input static tasks without changing the official
evaluation scores.
"""

from __future__ import annotations

import csv
import html
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize, TwoSlopeNorm
from matplotlib.cm import ScalarMappable


ROOT = Path("outputs/bio_phys_30_gpt56sol_20260921")
PACK = ROOT / "02_packaged/20260922"
GALLERY = ROOT / "03_plots/LLM_vs_truth_20260922/gpt56sol_20260922_55x3"


def stable_norm(values: np.ndarray) -> Normalize:
    values = np.asarray(values, dtype=float)
    low = float(np.nanmin(values))
    high = float(np.nanmax(values))
    if not np.isfinite(low) or not np.isfinite(high):
        return Normalize(0.0, 1.0)
    if high <= low:
        delta = max(abs(low) * 1e-6, 1e-9)
        return Normalize(low - delta, high + delta)
    return Normalize(low, high)


def residual_norm(values: np.ndarray) -> TwoSlopeNorm:
    values = np.asarray(values, dtype=float)
    finite = values[np.isfinite(values)]
    radius = float(np.max(np.abs(finite))) if len(finite) else 1.0
    radius = max(radius, 1e-12)
    return TwoSlopeNorm(vmin=-radius, vcenter=0.0, vmax=radius)


def normalize_coordinates(frame: pd.DataFrame, features: list[str]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    raw = frame[features].to_numpy(dtype=float)
    low = np.nanmin(raw, axis=0)
    high = np.nanmax(raw, axis=0)
    span = high - low
    span[span == 0] = 1.0
    return (raw - low) / span, low, high


def scatter3d(ax, coordinates, values, value_norm, cmap, title, features, mask):
    shown = mask & np.isfinite(values)
    if not np.any(shown):
        ax.set_title(title + " (no finite points)")
        return
    ax.scatter(
        coordinates[shown, 0],
        coordinates[shown, 1],
        coordinates[shown, 2],
        c=values[shown],
        cmap=cmap,
        norm=value_norm,
        s=8,
        alpha=0.72,
        linewidths=0,
        rasterized=True,
    )
    ax.set(
        xlabel=f"norm({features[0]})",
        ylabel=f"norm({features[1]})",
        zlabel=f"norm({features[2]})",
        title=title,
        xlim=(0, 1),
        ylim=(0, 1),
        zlim=(0, 1),
    )
    ax.view_init(elev=25, azim=-55)
    ax.grid(alpha=0.2)


def slice_masks(coordinate: np.ndarray) -> tuple[list[np.ndarray], list[str]]:
    """Return three nonempty quantile slices for the fourth input."""
    q = np.nanquantile(coordinate, [0.0, 1 / 3, 2 / 3, 1.0])
    # Quantile boundaries can coincide for repeated coordinates.  Rank bins
    # keep the display useful while preserving the ordering of the fourth axis.
    order = np.argsort(coordinate, kind="stable")
    bins = np.empty(len(coordinate), dtype=int)
    bins[order] = np.minimum(np.arange(len(coordinate)) * 3 // max(len(coordinate), 1), 2)
    masks = [bins == i for i in range(3)]
    labels = [
        f"low {q[0]:.3g}–{q[1]:.3g}",
        f"middle {q[1]:.3g}–{q[2]:.3g}",
        f"high {q[2]:.3g}–{q[3]:.3g}",
    ]
    return masks, labels


def plot_three_dimensional(frame: pd.DataFrame, features: list[str], title: str, destination: Path) -> dict:
    coordinates, low, high = normalize_coordinates(frame, features)
    truth = frame["ground_truth"].to_numpy(dtype=float)
    prediction = frame["prediction"].to_numpy(dtype=float)
    residual = frame["residual"].to_numpy(dtype=float)
    finite = np.isfinite(coordinates).all(axis=1)
    truth_prediction_norm = stable_norm(np.concatenate([truth[finite], prediction[finite]]))
    residual_scale = residual_norm(residual[finite])

    fig = plt.figure(figsize=(15, 10), constrained_layout=True)
    axes = [
        fig.add_subplot(2, 2, 1, projection="3d"),
        fig.add_subplot(2, 2, 2, projection="3d"),
        fig.add_subplot(2, 2, 3, projection="3d"),
        fig.add_subplot(2, 2, 4),
    ]
    scatter3d(axes[0], coordinates, truth, truth_prediction_norm, "viridis", "Ground truth (color = target)", features, finite)
    scatter3d(axes[1], coordinates, prediction, truth_prediction_norm, "viridis", "LLM solution (color = target)", features, finite)
    scatter3d(axes[2], coordinates, residual, residual_scale, "coolwarm", "Residual (prediction − truth)", features, finite)

    axes[3].scatter(truth[finite], prediction[finite], s=8, alpha=0.5, color="#3b6ea8", rasterized=True)
    lo = float(np.nanmin(np.concatenate([truth[finite], prediction[finite]])))
    hi = float(np.nanmax(np.concatenate([truth[finite], prediction[finite]])))
    axes[3].plot([lo, hi], [lo, hi], "--", color="#a94b4b", lw=1.2, label="identity")
    axes[3].set(xlabel="ground truth", ylabel="LLM prediction", title="Pointwise agreement")
    axes[3].legend(frameon=False, fontsize=8)
    axes[3].grid(alpha=0.15)
    fig.colorbar(ScalarMappable(norm=truth_prediction_norm, cmap="viridis"), ax=axes[:2], shrink=0.78, label="target value")
    fig.colorbar(ScalarMappable(norm=residual_scale, cmap="coolwarm"), ax=axes[2], shrink=0.78, label="residual")
    fig.suptitle(
        f"{title}\n3-input static function; coordinates normalized independently to [0, 1]",
        fontsize=13,
    )
    fig.savefig(destination / "highdim.png", dpi=170, bbox_inches="tight")
    fig.savefig(destination / "highdim.pdf", bbox_inches="tight")
    plt.close(fig)
    return {"input_dimension": 3, "features": features, "normalization_min": low.tolist(), "normalization_max": high.tolist(), "plots": ["highdim"]}


def plot_four_dimensional(frame: pd.DataFrame, features: list[str], title: str, destination: Path) -> dict:
    coordinates, low, high = normalize_coordinates(frame, features)
    truth = frame["ground_truth"].to_numpy(dtype=float)
    prediction = frame["prediction"].to_numpy(dtype=float)
    residual = frame["residual"].to_numpy(dtype=float)
    finite = np.isfinite(coordinates).all(axis=1)
    slices, slice_labels = slice_masks(coordinates[:, 3])
    truth_prediction_norm = stable_norm(np.concatenate([truth[finite], prediction[finite]]))
    residual_scale = residual_norm(residual[finite])

    fig = plt.figure(figsize=(17, 13), constrained_layout=True)
    grid = fig.add_gridspec(3, 4, width_ratios=[1, 1, 1, 0.95])
    truth_axes, prediction_axes, residual_axes = [], [], []
    for col, (part, label_text) in enumerate(zip(slices, slice_labels)):
        mask = finite & part
        ax = fig.add_subplot(grid[0, col], projection="3d")
        scatter3d(ax, coordinates[:, :3], truth, truth_prediction_norm, "viridis", f"Truth | {label_text}", features[:3], mask)
        truth_axes.append(ax)
        ax = fig.add_subplot(grid[1, col], projection="3d")
        scatter3d(ax, coordinates[:, :3], prediction, truth_prediction_norm, "viridis", f"Prediction | {label_text}", features[:3], mask)
        prediction_axes.append(ax)
        ax = fig.add_subplot(grid[2, col], projection="3d")
        scatter3d(ax, coordinates[:, :3], residual, residual_scale, "coolwarm", f"Residual | {label_text}", features[:3], mask)
        residual_axes.append(ax)

    agreement = fig.add_subplot(grid[0, 3])
    agreement.scatter(truth[finite], prediction[finite], c=coordinates[finite, 3], cmap="plasma", s=7, alpha=0.5, rasterized=True)
    lo = float(np.nanmin(np.concatenate([truth[finite], prediction[finite]])))
    hi = float(np.nanmax(np.concatenate([truth[finite], prediction[finite]])))
    agreement.plot([lo, hi], [lo, hi], "--", color="#a94b4b", lw=1.2)
    agreement.set(xlabel="truth", ylabel="prediction", title=f"Agreement\ncolor = norm({features[3]})")
    agreement.grid(alpha=0.15)

    pair = fig.add_subplot(grid[1, 3])
    pair.scatter(coordinates[finite, 0], coordinates[finite, 3], c=truth[finite], cmap="viridis", norm=truth_prediction_norm, s=7, alpha=0.5, rasterized=True)
    pair.set(xlabel=f"norm({features[0]})", ylabel=f"norm({features[3]})", title="Truth over 4D projection")
    pair.grid(alpha=0.15)

    residual_ax = fig.add_subplot(grid[2, 3])
    residual_ax.scatter(coordinates[finite, 0], coordinates[finite, 3], c=residual[finite], cmap="coolwarm", norm=residual_scale, s=7, alpha=0.5, rasterized=True)
    residual_ax.set(xlabel=f"norm({features[0]})", ylabel=f"norm({features[3]})", title="Residual over 4D projection")
    residual_ax.grid(alpha=0.15)

    fig.colorbar(ScalarMappable(norm=truth_prediction_norm, cmap="viridis"), ax=truth_axes + prediction_axes + [pair], shrink=0.76, label="target value")
    fig.colorbar(ScalarMappable(norm=residual_scale, cmap="coolwarm"), ax=residual_axes + [residual_ax], shrink=0.76, label="residual")
    fig.suptitle(
        f"{title}\n4-input static function; first three inputs are 3D coordinates and the fourth is shown by slices/color",
        fontsize=13,
    )
    fig.savefig(destination / "highdim.png", dpi=170, bbox_inches="tight")
    fig.savefig(destination / "highdim.pdf", bbox_inches="tight")
    plt.close(fig)
    return {
        "input_dimension": 4,
        "features": features,
        "normalization_min": low.tolist(),
        "normalization_max": high.tolist(),
        "fourth_axis_slices": slice_labels,
        "plots": ["highdim"],
    }


def load_score_rows() -> list[dict]:
    with (GALLERY / "score_table.csv").open(newline="") as stream:
        return list(csv.DictReader(stream))


def build_focus_index(rows: list[dict], dimensions: dict[str, dict]) -> None:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["task"], []).append(row)
    records = []
    for task, task_rows in sorted(grouped.items()):
        scores = [float(item["official_reward"]) for item in sorted(task_rows, key=lambda x: x["run"])]
        mean = sum(scores) / len(scores)
        info = dimensions[task]
        records.append({"task": task, "family": info["family"], "input_dimension": info["input_dimension"], "features": ",".join(info["features"]), "run_01": scores[0], "run_02": scores[1], "run_03": scores[2], "mean_official_reward": mean})
    fields = ["task", "family", "input_dimension", "features", "run_01", "run_02", "run_03", "mean_official_reward"]
    with (GALLERY / "task_score_summary.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)
    focus = [record for record in records if record["mean_official_reward"] < 0.98]
    focus_set = {record["task"] for record in focus}
    body = []
    for record in focus:
        task = record["task"]
        task_rows = sorted(grouped[task], key=lambda x: x["run"])
        cells = []
        for row in task_rows:
            rel = row["plot_dir"]
            solution = GALLERY / rel
            image = Path(rel) / "comparison.png"
            links = [f'<a href="{html.escape(image.as_posix())}">comparison</a>']
            for name in ("highdim.png", "spatial.png"):
                if (solution / name).exists():
                    links.append(f'<a href="{html.escape((Path(rel) / name).as_posix())}">{name[:-4]}</a>')
            cells.append(f'<td><b>{html.escape(row["run"])}</b><br>official {float(row["official_reward"]):.6g}<br>{" · ".join(links)}<br><span class="status">{html.escape(row["plot_status"])}</span></td>')
        body.append(f'<tr><th>{html.escape(task)}</th><td>{record["family"]}, {record["input_dimension"]} inputs<br>{html.escape(record["features"])}</td>{"".join(cells)}<td><b>{record["mean_official_reward"]:.6g}</b></td></tr>')
    document = f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SRBench low-mean focus</title><style>
body{{font:15px/1.5 system-ui,sans-serif;color:#172033;background:#f6f8fb;margin:24px}}h1{{margin:0 0 8px}}p{{color:#526173}}table{{border-collapse:collapse;width:100%;background:#fff}}th,td{{border:1px solid #d8dee8;padding:10px;vertical-align:top;text-align:left}}th{{white-space:nowrap}}a{{color:#1d5d9b;text-decoration:none}}a:hover{{text-decoration:underline}}.status{{color:#a33}}.note{{margin:12px 0 18px}}
</style><h1>均值低于 0.98 的题目</h1><p class="note">均值为三次官方 reward 的算术平均。点击 comparison 查看标准图；若有 highdim，可查看补充的三维/四维静态图。共 {len(focus)} 题。</p>
<table><thead><tr><th>题目</th><th>类型 / 输入</th><th>Run 01</th><th>Run 02</th><th>Run 03</th><th>三次均值</th></tr></thead><tbody>{''.join(body)}</tbody></table>
<p>完整 55 题总览：<a href="index.html">index.html</a></p></html>'''
    (GALLERY / "low_mean_index.html").write_text(document, encoding="utf-8")


def main() -> None:
    rows = load_score_rows()
    dimensions: dict[str, dict] = {}
    generated = 0
    skipped = []
    for task_dir in sorted(PACK.iterdir()):
        if not task_dir.is_dir() or not (task_dir / "manifest.json").exists():
            continue
        manifest = json.loads((task_dir / "manifest.json").read_text())
        contract = manifest["contract"]
        dimensions[task_dir.name] = {"family": contract["family"], "input_dimension": len(contract["features"]), "features": contract["features"]}
        if contract["family"] != "static" or len(contract["features"]) not in (3, 4):
            continue
        task_rows = [row for row in rows if row["task"] == task_dir.name]
        for row in task_rows:
            solution = GALLERY / row["plot_dir"]
            pred_path = solution / "predictions.csv"
            if not pred_path.exists() or row["plot_status"] != "ok":
                skipped.append(f"{task_dir.name}/{row['run']}")
                continue
            frame = pd.read_csv(pred_path)
            title = f"{task_dir.name} | {row['run']} | official reward = {float(row['official_reward']):.6f}"
            if len(contract["features"]) == 3:
                metadata = plot_three_dimensional(frame, contract["features"], title, solution)
            else:
                metadata = plot_four_dimensional(frame, contract["features"], title, solution)
            (solution / "highdim_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            generated += 1
    build_focus_index(rows, dimensions)
    print(f"generated high-dimensional plots: {generated}; skipped: {len(skipped)}")
    if skipped:
        print("skipped:", ", ".join(skipped))


if __name__ == "__main__":
    main()
