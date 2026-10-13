"""Plot the measured low-score replay trials without changing submissions.

The official Daytona evaluator exposes ``/app/data``.  Some submitted laws
depend on that path (or on ``data/`` beside ``law.py``), so this script builds
an isolated, plotting-only adapter for each such law.  The adapter is never
used for scoring and the generated metrics retain the original law path.
"""

from __future__ import annotations

import ast
import concurrent.futures
import json
import math
import os
import pathlib
import subprocess
import time
from typing import Any


REPO = pathlib.Path(__file__).resolve().parent
PYTHON = "/Users/hubertlinhong/miniconda3/envs/srbench-agent/bin/python"
MODEL = "gpt-5.6-sol"
CONFIGS = {
    "0917": {
        "eval": REPO / "outputs/bio_phys_replay_0917_gpt54_20260929/04_evaluations/gpt56sol_replay0917_all59_x3",
        "pack": REPO / "outputs/bio_phys_replay_0917_gpt54_20260929/02_packaged/20260930",
        "plot": REPO / "outputs/bio_phys_replay_0917_gpt54_20260929/03_plots/LLM_vs_truth_20261001/gpt56sol_replay0917_all59_x3",
    },
    "0921": {
        "eval": REPO / "outputs/bio_phys_replay_0921_gpt54_20260929/04_evaluations/gpt56sol_replay0921_all59_x3",
        "pack": REPO / "outputs/bio_phys_replay_0921_gpt54_20260929/02_packaged/20260930",
        "plot": REPO / "outputs/bio_phys_replay_0921_gpt54_20260929/03_plots/LLM_vs_truth_20261001/gpt56sol_replay0921_all59_x3",
    },
}


def _read(path: pathlib.Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _score(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _trials(config: dict[str, pathlib.Path]) -> tuple[dict[str, list[dict[str, Any]]], set[str]]:
    """Return all trial records and tasks with at least one score below .9."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for trial_dir in sorted(config["eval"].glob("task__*")):
        result_path = trial_dir / "result.json"
        if not result_path.is_file():
            continue
        result = _read(result_path)
        task = pathlib.Path(result.get("task_id", {}).get("path", "")).name
        if not task:
            continue
        metrics_path = trial_dir / "verifier" / "metrics.json"
        metrics = _read(metrics_path) if metrics_path.is_file() else {}
        record = {
            "task": task,
            "trial": trial_dir.name,
            "directory": trial_dir,
            "started": result.get("started_at", ""),
            "score": metrics.get("raw_r2"),
            "has_score": _score(metrics.get("raw_r2")),
        }
        grouped.setdefault(task, []).append(record)
    for records in grouped.values():
        records.sort(key=lambda item: (item["started"], item["trial"]))
    low = {
        task for task, records in grouped.items()
        if any(item["has_score"] and item["score"] < 0.9 for item in records)
    }
    return grouped, low


def _insert_import_path(source: str, adapter: pathlib.Path) -> str:
    """Make local sibling imports work while preserving future imports."""
    prefix = "import sys as _plot_sys\n_plot_sys.path.insert(0, %r)\n" % str(adapter)
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return prefix + source
    insert_line = 0
    for node in tree.body:
        is_docstring = isinstance(node, ast.Expr) and isinstance(
            getattr(node, "value", None), ast.Constant
        ) and isinstance(node.value.value, str)
        is_future = isinstance(node, ast.ImportFrom) and node.module == "__future__"
        if is_docstring or is_future:
            insert_line = max(insert_line, int(getattr(node, "end_lineno", 0)))
            continue
        break
    lines = source.splitlines(keepends=True)
    return "".join(lines[:insert_line]) + prefix + "".join(lines[insert_line:])


def _adapter(config: dict[str, pathlib.Path], task: str, trial: str) -> tuple[pathlib.Path, pathlib.Path]:
    """Create a plotting-only law directory and return (adapter, original)."""
    trial_dir = config["eval"] / trial
    original = (trial_dir / "artifacts" / "app" / "law.py").resolve()
    if not original.is_file():
        raise FileNotFoundError(original)
    adapter = config["plot"] / "_plot_adapters" / f"{task}__{trial}"
    adapter.mkdir(parents=True, exist_ok=True)
    package_task = (config["pack"] / task / "task").resolve()
    environment = package_task / "environment"
    data_link = adapter / "data"
    if not data_link.exists():
        os.symlink(str(environment), str(data_link), target_is_directory=True)
    for sibling in original.parent.iterdir():
        if sibling.name in {"law.py", "data"}:
            continue
        destination = adapter / sibling.name
        if destination.exists() or destination.is_symlink():
            continue
        os.symlink(str(sibling.resolve()), str(destination), target_is_directory=sibling.is_dir())
    source = original.read_text(encoding="utf-8", errors="replace")
    # Literal /app paths are rewritten only in this temporary plotting copy.
    source = source.replace("/app", str(adapter.resolve()))
    (adapter / "law.py").write_text(_insert_import_path(source, adapter.resolve()), encoding="utf-8")
    return adapter, original


def _output_dir(config: dict[str, pathlib.Path], task: str, trial: str, run_number: int) -> pathlib.Path:
    existing = sorted((config["plot"] / task).glob(f"run_*_{trial}"))
    if existing:
        return existing[0]
    return config["plot"] / task / f"run_{run_number:02d}_{trial}"


def _patch_provenance(output: pathlib.Path, original: pathlib.Path, adapter: pathlib.Path,
                      score: float, partition: str) -> None:
    metrics_path = output / "metrics.json"
    if not metrics_path.is_file():
        return
    metrics = _read(metrics_path)
    metrics["law"] = str(original)
    metrics["official_evaluation_raw_r2"] = score
    metrics["plot_partition"] = partition
    metrics["plot_adapter"] = str(adapter)
    metrics_path.write_text(json.dumps(metrics, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _run_plot(config: dict[str, pathlib.Path], item: dict[str, Any], run_number: int) -> dict[str, Any]:
    task = item["task"]
    trial = item["trial"]
    score = float(item["score"])
    output = _output_dir(config, task, trial, run_number)
    output.mkdir(parents=True, exist_ok=True)
    if (output / "comparison.png").is_file() and (output / "predictions.csv").is_file():
        return {"task": task, "trial": trial, "score": score, "output": str(output), "status": "existing"}
    started = time.time()
    adapter = None
    original = None
    attempts = []
    try:
        adapter, original = _adapter(config, task, trial)
        for partition in ("both", "test"):
            command = [
                PYTHON, "-m", "srbench", "plot",
                "--package", str((config["pack"] / task).resolve()),
                "--law", str((adapter / "law.py").resolve()),
                "--output", str(output.resolve()),
                "--partition", partition,
                "--title", f"{task} | run_{run_number:02d} | {trial}",
                "--score=" + repr(score),
                "--model", MODEL,
            ]
            try:
                process = subprocess.run(
                    command,
                    cwd=str(REPO),
                    env={**os.environ, "PYTHONPATH": "src", "MPLBACKEND": "Agg"},
                    text=True,
                    capture_output=True,
                    timeout=900,
                )
                attempts.append({
                    "partition": partition,
                    "returncode": process.returncode,
                    "stdout": process.stdout[-2000:],
                    "stderr": process.stderr[-4000:],
                })
            except Exception as exc:  # pragma: no cover - defensive batch logging
                attempts.append({"partition": partition, "error": repr(exc)})
                process = None
            if process is not None and process.returncode == 0 and (output / "comparison.png").is_file():
                _patch_provenance(output, original, adapter, score, partition)
                return {
                    "task": task, "trial": trial, "score": score,
                    "output": str(output), "status": "ok", "partition": partition,
                    "seconds": round(time.time() - started, 2), "attempts": attempts,
                }
        return {
            "task": task, "trial": trial, "score": score, "output": str(output),
            "status": "failed", "seconds": round(time.time() - started, 2), "attempts": attempts,
        }
    except Exception as exc:
        return {
            "task": task, "trial": trial, "score": score, "output": str(output),
            "status": "failed", "seconds": round(time.time() - started, 2),
            "attempts": attempts, "error": repr(exc),
        }


def _highdim(config: dict[str, pathlib.Path], record: dict[str, Any]) -> dict[str, Any]:
    output = pathlib.Path(record["output"])
    task = record["task"]
    manifest = _read(config["pack"] / task / "manifest.json")
    contract = manifest.get("contract", {})
    features = contract.get("features", [])
    if contract.get("family") != "static" or len(features) < 3:
        return {"task": task, "output": str(output), "status": "not_applicable"}
    prediction = output / "predictions.csv"
    if not prediction.is_file():
        return {"task": task, "output": str(output), "status": "missing_predictions"}
    command = [
        PYTHON, "skills/srbench-plot/scripts/plot_cached_highdim.py",
        "--predictions", str(prediction), "--features", *features,
        "--output", str(output),
        "--title", f"{task} | {pathlib.Path(output).name} | conditional slices",
    ]
    try:
        process = subprocess.run(
            command, cwd=str(REPO), env={**os.environ, "MPLBACKEND": "Agg"},
            text=True, capture_output=True, timeout=300,
        )
        return {
            "task": task, "output": str(output),
            "status": "ok" if process.returncode == 0 else "failed",
            "returncode": process.returncode,
            "stderr": process.stderr[-3000:],
        }
    except Exception as exc:
        return {"task": task, "output": str(output), "status": "failed", "error": repr(exc)}


def main() -> None:
    all_logs = {}
    for label, config in CONFIGS.items():
        config["plot"].mkdir(parents=True, exist_ok=True)
        grouped, low_tasks = _trials(config)
        jobs = []
        for task in sorted(low_tasks):
            for run_number, item in enumerate(grouped[task], 1):
                if item["has_score"]:
                    jobs.append((task, run_number, item))
        print(f"{label}: {len(low_tasks)} low tasks, {len(jobs)} scored trials", flush=True)
        plot_logs = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            futures = [pool.submit(_run_plot, config, item, run_number)
                       for task, run_number, item in jobs]
            for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
                result = future.result()
                plot_logs.append(result)
                print(f"[{label} {index}/{len(futures)}] {result['status']} "
                      f"{result['task']} {result['trial']}", flush=True)
        plot_logs.sort(key=lambda x: (x["task"], x["trial"]))
        highdim_logs = []
        for record in plot_logs:
            if record["status"] in {"ok", "existing"}:
                highdim_logs.append(_highdim(config, record))
        manifest = {
            "threshold": 0.9,
            "low_tasks": sorted(low_tasks),
            "plots": plot_logs,
            "highdim": highdim_logs,
            "ground_truth_atlas": str((config["plot"].parent.parent / "solution_20260930").resolve()),
        }
        (config["plot"] / "low_score_manifest.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        all_logs[label] = manifest
        ok = sum(item["status"] in {"ok", "existing"} for item in plot_logs)
        print(f"{label}: comparison plots available {ok}/{len(plot_logs)}", flush=True)
    print(json.dumps({label: {"low_tasks": data["low_tasks"]} for label, data in all_logs.items()},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
