"""Run the standard SRBench comparison plot for every recoverable submission."""

from __future__ import annotations

import concurrent.futures
import json
import pathlib
import subprocess
import sys
import time


ROOT = pathlib.Path("outputs/bio_phys_30_gpt56sol_20260921")
EVAL = ROOT / "04_evaluations/gpt56sol_20260922_55x3"
PLOT = ROOT / "03_plots/LLM_vs_truth_20260922/gpt56sol_20260922_55x3"
PACK = ROOT / "02_packaged/20260922"
PYTHON = "/Users/hubertlinhong/miniconda3/envs/srbench-agent/bin/python"


def score_for(trial: str) -> float:
    result = json.loads((EVAL / trial / "result.json").read_text())
    return float(result["verifier_result"]["rewards"]["reward"])


def one(item: tuple[pathlib.Path, str, str, float]) -> dict:
    solution, task, trial, score = item
    run = solution.name.split("_task__", 1)[0]
    package = PACK / task
    title = f"{task} | {run} | {trial}"
    command = [
        PYTHON, "-m", "srbench", "plot",
        "--package", str(package.resolve()),
        "--law", str((solution / "law.py").resolve()),
        "--output", str(solution.resolve()),
        "--title", title,
        "--score", repr(score),
        "--model", "gpt-5.6-sol",
    ]
    started = time.time()
    try:
        proc = subprocess.run(
            command,
            cwd=pathlib.Path.cwd(),
            env={**__import__("os").environ, "PYTHONPATH": "src"},
            text=True,
            capture_output=True,
            timeout=600,
        )
        return {
            "task": task, "run": run, "trial": trial, "score": score,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "seconds": round(time.time() - started, 3),
            "stdout": proc.stdout[-2000:], "stderr": proc.stderr[-4000:],
        }
    except Exception as exc:
        return {
            "task": task, "run": run, "trial": trial, "score": score,
            "ok": False, "returncode": None,
            "seconds": round(time.time() - started, 3),
            "stdout": "", "stderr": repr(exc),
        }


def main() -> None:
    jobs = []
    for task_dir in sorted(PLOT.iterdir()):
        if not task_dir.is_dir() or task_dir.name == "_index":
            continue
        for solution in sorted((task_dir / "solutions").glob("run_*_task__*")):
            law = solution / "law.py"
            if not law.is_file():
                continue
            trial = "task__" + solution.name.split("_task__", 1)[1]
            jobs.append((solution, task_dir.name, trial, score_for(trial)))
    print(f"plot jobs: {len(jobs)}", flush=True)
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(one, item): item for item in jobs}
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            results.append(result)
            status = "OK" if result["ok"] else "FAIL"
            print(f"[{index}/{len(jobs)}] {status} {result['task']} {result['run']} "
                  f"({result['seconds']}s)", flush=True)
    results.sort(key=lambda x: (x["task"], x["run"]))
    (PLOT / "batch_plot_log.json").write_text(json.dumps(results, indent=2, ensure_ascii=True))
    failed = [x for x in results if not x["ok"]]
    print(f"completed: {len(results) - len(failed)}/{len(results)}; failed: {len(failed)}")
    for item in failed:
        print(item["task"], item["run"], item["trial"], item["stderr"][-500:])
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
