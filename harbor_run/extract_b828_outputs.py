#!/usr/bin/env python3
"""Extract every Bench_test_8.28 trial artefact and score both models fairly.

`law.py` never leaves the container; `tests/test.sh` prints it into
``verifier/test-stdout.txt`` fenced by ``---- LAW BEGIN/END ----``, so that file
is the only record of what the agent actually submitted.  This pulls the law and
explanation back out as real files, then aggregates.

Reporting choices, both forced by `harbor_run/b828_task_audit.json`:

* **Median, not mean.**  17 of 25 tasks are flagged high artifact risk; several
  holdouts have `var_test/var_train` as low as 6.9e-06, so a tiny absolute error
  becomes a reward of -2.5e8.  A mean over those is a report on the worst task's
  variance, not on the model.
* **Clipped R2 as the headline.**  `max(-1, min(1, r))` bounds each task's
  contribution, which is what makes a cross-task average meaningful at all.

Per-task win/loss uses the clipped value and only counts a task when both models
produced a score for it.

Usage: extract_b828_outputs.py <jobs_dir> <out_dir>
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import statistics
import sys
from collections import defaultdict
from pathlib import Path

# A retry job re-runs only the tasks whose trials died; later jobs win only when
# they actually produced a reward.
JOBS = {
    "opus-4.8": ["b828_opus48", "b828_opus48_retry"],
    "haiku-4.5": ["b828_haiku45", "b828_haiku45_retry"],
}
AUDIT = Path("/data1/SRBench/harbor_run/b828_task_audit.json")


def fenced(text: str, name: str) -> str | None:
    m = re.search(rf"^-+ {name} BEGIN -+$\n(.*?)^-+ {name} END -+$", text, re.S | re.M)
    return m.group(1) if m else None


def task_of(trial: Path) -> str | None:
    try:
        cfg = json.loads((trial / "config.json").read_text())
    except Exception:
        return None
    for key in ("task", "dataset"):
        node = cfg.get(key)
        if isinstance(node, dict) and node.get("path"):
            return Path(node["path"]).name
    # Harbor names trial dirs "<task-prefix>__<id>"; fall back to that.
    return trial.name.rsplit("__", 1)[0] or None


def clip(r: float) -> float:
    return max(-1.0, min(1.0, r))


def main() -> int:
    jobs_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    audit = {}
    if AUDIT.exists():
        audit = {r["task"]: r for r in json.loads(AUDIT.read_text())}

    # (model, task) -> list of per-attempt records
    per: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    trial_rows: list[dict[str, object]] = []

    for model, job_names in JOBS.items():
        for job_name in job_names:
            job = jobs_dir / job_name
            if not job.is_dir():
                continue
            for trial in sorted(p for p in job.iterdir() if p.is_dir()):
                task = task_of(trial)
                if not task:
                    continue
                row: dict[str, object] = {"model": model, "task": task,
                                          "trial": trial.name, "job": job_name}
                reward_file = trial / "verifier" / "reward.txt"
                if not reward_file.exists():
                    err = "ERROR"
                    exc = trial / "exception.txt"
                    if exc.exists():
                        found = re.findall(r"([A-Za-z]*(?:Timeout|Connection|Network|Setup|"
                                           r"Authentication|Api[A-Za-z]*)[A-Za-z]*Error)",
                                           exc.read_text())
                        err = found[-1] if found else "ERROR"
                    row["status"] = err
                    trial_rows.append(row)
                    continue

                try:
                    reward = float(reward_file.read_text().strip())
                except ValueError:
                    row["status"] = "UNPARSEABLE_REWARD"
                    trial_rows.append(row)
                    continue

                row["status"] = "scored"
                row["raw_r2"] = reward
                row["clipped_r2"] = clip(reward)

                dest = out_dir / model / task / trial.name
                dest.mkdir(parents=True, exist_ok=True)
                (dest / "reward.txt").write_text(f"{reward}\n")

                stdout = trial / "verifier" / "test-stdout.txt"
                if stdout.exists():
                    text = stdout.read_text(errors="replace")
                    law, explain = fenced(text, "LAW"), fenced(text, "EXPLAIN")
                    if law:
                        (dest / "law.py").write_text(law)
                        row["law_bytes"] = len(law)
                        # A law that ships an interpolator or hundreds of constants is a
                        # table, not a discovered formula -- the ushape run's key finding.
                        row["uses_interpolator"] = any(
                            k in law for k in ("CubicSpline", "interp1d", "UnivariateSpline",
                                               "PchipInterpolator", "Akima1D", "RBFInterpolator"))
                        row["uses_poly_fit"] = ("polyval" in law) or ("polyfit" in law)
                        row["n_numeric_literals"] = len(
                            re.findall(r"-?\d+\.\d{3,}(?:[eE][+-]?\d+)?", law))
                    if explain:
                        (dest / "explain.md").write_text(explain)
                    shutil.copy(stdout, dest / "verifier_stdout.txt")

                res = trial / "result.json"
                if res.exists():
                    d = json.loads(res.read_text())
                    ar = d.get("agent_result") or {}
                    row["cost_usd"] = ar.get("cost_usd")
                    row["n_output_tokens"] = ar.get("n_output_tokens")
                    (dest / "trial_meta.json").write_text(json.dumps(row, indent=2) + "\n")

                per[(model, task)].append(row)
                trial_rows.append(row)

    # --- per-trial CSV -------------------------------------------------------
    trial_cols = ["model", "task", "trial", "job", "status", "raw_r2", "clipped_r2",
                  "uses_interpolator", "uses_poly_fit", "n_numeric_literals",
                  "law_bytes", "cost_usd", "n_output_tokens"]
    with (out_dir / "trials.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=trial_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(trial_rows, key=lambda r: (r["task"], r["model"], r["trial"])))

    # --- per-task summary ---------------------------------------------------
    tasks = sorted({t for _, t in per} | {r["task"] for r in trial_rows})
    task_rows = []
    for task in tasks:
        row: dict[str, object] = {"task": task}
        a = audit.get(task, {})
        row["artifact_risk"] = a.get("artifact_risk", "")
        row["var_ratio"] = a.get("var_ratio", "")
        row["holdout_kind"] = a.get("holdout_kind", "")
        row["best_dumb_baseline_r2"] = a.get("best_baseline_r2", "")
        for model in JOBS:
            got = [r for r in per.get((model, task), []) if r.get("status") == "scored"]
            row[f"{model}_n"] = len(got)
            if got:
                cl = sorted(float(r["clipped_r2"]) for r in got)
                raw = sorted(float(r["raw_r2"]) for r in got)
                row[f"{model}_median_clipped"] = statistics.median(cl)
                row[f"{model}_best_clipped"] = cl[-1]
                row[f"{model}_median_raw"] = statistics.median(raw)
                row[f"{model}_worst_raw"] = raw[0]
                costs = [r["cost_usd"] for r in got if r.get("cost_usd") is not None]
                row[f"{model}_cost_usd"] = sum(costs) if costs else None
                row[f"{model}_any_interpolator"] = any(r.get("uses_interpolator") for r in got)
        o, h = row.get("opus-4.8_median_clipped"), row.get("haiku-4.5_median_clipped")
        if o is not None and h is not None:
            row["winner"] = "opus" if o > h + 1e-9 else "haiku" if h > o + 1e-9 else "tie"
            row["margin"] = float(o) - float(h)
        task_rows.append(row)

    task_cols = ["task", "artifact_risk", "holdout_kind", "var_ratio", "best_dumb_baseline_r2"]
    for m in JOBS:
        task_cols += [f"{m}_n", f"{m}_median_clipped", f"{m}_best_clipped", f"{m}_median_raw",
                      f"{m}_worst_raw", f"{m}_cost_usd", f"{m}_any_interpolator"]
    task_cols += ["winner", "margin"]
    with (out_dir / "by_task.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=task_cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(task_rows)

    # --- headline ------------------------------------------------------------
    summary: dict[str, object] = {"n_tasks": len(tasks), "by_model": {}}
    for model in JOBS:
        scored = [r for r in trial_rows if r["model"] == model and r.get("status") == "scored"]
        errored = [r for r in trial_rows if r["model"] == model and r.get("status") not in
                   ("scored", None)]
        if not scored:
            continue
        med_by_task = [float(r[f"{model}_median_clipped"]) for r in task_rows
                       if r.get(f"{model}_median_clipped") is not None]
        costs = [r["cost_usd"] for r in scored if r.get("cost_usd") is not None]
        summary["by_model"][model] = {
            "n_trials_scored": len(scored),
            "n_trials_errored": len(errored),
            "error_kinds": dict(sorted(
                (k, sum(1 for r in errored if r.get("status") == k))
                for k in {str(r.get("status")) for r in errored})) if errored else {},
            "macro_median_clipped_r2": statistics.fmean(med_by_task) if med_by_task else None,
            "median_of_task_medians_clipped": statistics.median(med_by_task) if med_by_task else None,
            "n_tasks_clipped_ge_0.9": sum(1 for v in med_by_task if v >= 0.9),
            "n_tasks_clipped_le_0": sum(1 for v in med_by_task if v <= 0.0),
            "total_cost_usd": sum(costs) if costs else None,
            "n_trials_with_interpolator": sum(1 for r in scored if r.get("uses_interpolator")),
        }
    both = [r for r in task_rows if r.get("winner")]
    summary["head_to_head"] = {
        "n_tasks_compared": len(both),
        "opus_wins": sum(1 for r in both if r["winner"] == "opus"),
        "haiku_wins": sum(1 for r in both if r["winner"] == "haiku"),
        "ties": sum(1 for r in both if r["winner"] == "tie"),
    }
    risky = {r["task"] for r in task_rows if r.get("artifact_risk") == "high"}
    clean = [r for r in both if r["task"] not in risky]
    summary["head_to_head_clean_tasks_only"] = {
        "n_tasks": len(clean),
        "opus_wins": sum(1 for r in clean if r["winner"] == "opus"),
        "haiku_wins": sum(1 for r in clean if r["winner"] == "haiku"),
        "ties": sum(1 for r in clean if r["winner"] == "tie"),
        "opus_macro_median_clipped": statistics.fmean(
            [float(r["opus-4.8_median_clipped"]) for r in clean]) if clean else None,
        "haiku_macro_median_clipped": statistics.fmean(
            [float(r["haiku-4.5_median_clipped"]) for r in clean]) if clean else None,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
