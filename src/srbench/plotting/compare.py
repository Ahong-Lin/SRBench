"""Compare a model's law.py with ground truth on the same train/test inputs."""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from srbench.common.contracts import contract_from_spec
from srbench.common.io import read_json, write_json, relative_artifact
from srbench.common.metrics import regression_metrics
from srbench.common.prediction import isolated_predictions
from srbench.packaging.reference import truth_values
from .figures import make_figure, make_spatial_figure, plot_metadata
from .paths import comparison_directory


def compare(package, law, output=None, reference=None, row_timeout=15.0, partition="both",
            title=None, score=None, model=None):
    package = Path(package).resolve()
    manifest = read_json(package / "manifest.json")
    paths = manifest["paths"]
    ground = read_json(relative_artifact(package, paths["ground_truth"]))
    split = read_json(relative_artifact(package, paths["split"]))
    split = plot_metadata(split, ground["spec"])
    typed_contract = contract_from_spec(ground["spec"])
    contract = manifest["contract"]
    if typed_contract.features != contract["features"] or typed_contract.target != contract["target"]:
        raise ValueError("manifest feature/target roles disagree with ground truth")
    if partition not in {"both", "train", "test"}:
        raise ValueError("partition must be both, train or test")
    partitions = ["train", "test"] if partition == "both" else [partition]
    frames = []
    for label in partitions:
        frame = pd.read_csv(relative_artifact(package, paths[label]))
        missing = set(contract["features"] + [contract["target"]]) - set(frame.columns)
        if missing:
            raise ValueError(f"data is missing declared columns: {sorted(missing)}")
        if not np.isfinite(frame[contract["features"] + [contract["target"]]].to_numpy(dtype=float)).all():
            raise ValueError("data contains nonfinite inputs or labels")
        frame["partition"] = label
        frames.append(frame)
    frame = pd.concat(frames, ignore_index=True)
    truth = truth_values(typed_contract, frame)
    rows = frame[contract["features"]].to_dict(orient="records")
    if reference:
        check = isolated_predictions(reference, rows, contract["target"], row_timeout=row_timeout, seed=0)
        if not check.ok:
            raise RuntimeError("reference law failed: " + check.errors[0]["error"])
        if not np.allclose(check.values, truth, rtol=1e-9, atol=1e-11):
            raise ValueError("provided reference disagrees with the packaged ground truth")
    result = isolated_predictions(law, rows, contract["target"], row_timeout=row_timeout, seed=0)
    if output is None:
        output = comparison_directory(package, manifest["task_id"])
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    result_frame = frame[["partition"] + contract["features"]].copy()
    result_frame["observed_label"] = frame[contract["target"]]
    result_frame["ground_truth"] = truth
    result_frame["prediction"] = [float(v) if v is not None else np.nan for v in result.values]
    result_frame["residual"] = result_frame["prediction"] - truth
    result_frame.to_csv(output / "predictions.csv", index=False)
    report = {"status": "prediction_failed" if not result.ok else "ok",
              "task_id": manifest["task_id"], "law": str(Path(law).resolve()),
              "truth": "mathematical expression in packaged ground_truth.json",
              "n_requested": len(frame), "n_evaluated": sum(v is not None for v in result.values),
              "errors": result.errors, "partitions": {}}
    if not result.ok:
        report["scores"] = None
        write_json(output / "metrics.json", report)
        # Avoid stale plots from a prior successful run beside a failure report.
        for suffix in ("png", "pdf"):
            (output / f"comparison.{suffix}").unlink(missing_ok=True)
            (output / f"spatial.{suffix}").unlink(missing_ok=True)
        raise RuntimeError(f"submitted law failed; details: {output / 'metrics.json'}")
    for label in partitions:
        selected = result_frame[result_frame["partition"] == label]
        report["partitions"][label] = {
            "versus_ground_truth": regression_metrics(selected["prediction"], selected["ground_truth"]),
            "versus_observed_label": regression_metrics(selected["prediction"], selected["observed_label"]),
        }
    report["official_test_raw_r2"] = (report["partitions"].get("test", {}).get("versus_observed_label", {}).get("raw_r2"))
    write_json(output / "metrics.json", report)
    figure_title = title or manifest["task_id"]
    if score is not None:
        figure_title += f" | test R² = {float(score):.6f}"
    if model:
        figure_title += f" | LLM: {model}"
    fig = make_figure(result_frame, contract, split, title=figure_title)
    fig.savefig(output / "comparison.png", dpi=180, bbox_inches="tight")
    fig.savefig(output / "comparison.pdf", bbox_inches="tight")
    import matplotlib.pyplot as plt
    plt.close(fig)
    if contract["family"] == "static" and len(contract["features"]) == 2:
        spatial = make_spatial_figure(result_frame, contract, split, title=figure_title)
        spatial.savefig(output / "spatial.png", dpi=180, bbox_inches="tight")
        spatial.savefig(output / "spatial.pdf", bbox_inches="tight")
        plt.close(spatial)
    return output


def main(argv=None):
    p = argparse.ArgumentParser(prog="srbench plot", description=__doc__)
    p.add_argument("--package", required=True, type=Path)
    p.add_argument("--law", required=True, type=Path)
    p.add_argument("--output", type=Path)
    p.add_argument("--reference", type=Path, help="optional reference law; must reproduce packaged ground truth")
    p.add_argument("--row-timeout", type=float, default=15.0)
    p.add_argument("--partition", choices=["both", "train", "test"], default="both")
    p.add_argument("--title", help="figure title prefix")
    p.add_argument("--score", type=float, help="score shown in the figure title")
    p.add_argument("--model", help="model name shown in the figure title")
    args = p.parse_args(argv)
    print(compare(args.package, args.law, args.output, args.reference, args.row_timeout,
                  args.partition, args.title, args.score, args.model))


if __name__ == "__main__":
    main()
