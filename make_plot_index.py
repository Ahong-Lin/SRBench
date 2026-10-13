"""Build a browsable 55-task gallery and a machine-readable score table."""

from __future__ import annotations

import csv
import html
import json
import pathlib
import re


ROOT = pathlib.Path("outputs/bio_phys_30_gpt56sol_20260921")
GALLERY = ROOT / "03_plots/LLM_vs_truth_20260922/gpt56sol_20260922_55x3"
EVAL = ROOT / "04_evaluations/gpt56sol_20260922_55x3"


def task_key(path: pathlib.Path) -> tuple[str, int]:
    match = re.match(r"(biology|physics)_(\d+)$", path.name)
    return (match.group(1), int(match.group(2))) if match else (path.name, 0)


def run_key(path: pathlib.Path) -> int:
    match = re.match(r"run_(\d+)_task__", path.name)
    return int(match.group(1)) if match else 99


def main() -> None:
    rows = []
    task_dirs = sorted(
        [p for p in GALLERY.iterdir() if p.is_dir() and re.match(r"(?:biology|physics)_\d+$", p.name)],
        key=task_key,
    )
    for task_dir in task_dirs:
        runs = sorted((task_dir / "solutions").glob("run_*_task__*"), key=run_key)
        task_rows = []
        for solution in runs:
            run_label, trial_suffix = solution.name.split("_task__", 1)
            trial = "task__" + trial_suffix
            result = json.loads((EVAL / trial / "result.json").read_text())
            official = float(result["verifier_result"]["rewards"]["reward"])
            metrics = json.loads((solution / "metrics.json").read_text())
            plot_r2 = metrics.get("official_test_raw_r2")
            if plot_r2 is None and metrics.get("partitions"):
                plot_r2 = metrics["partitions"].get("test", {}).get("versus_observed_label", {}).get("raw_r2")
            record = {
                "task": task_dir.name,
                "run": run_label,
                "trial": trial,
                "official_reward": official,
                "plot_status": metrics.get("status", "unknown"),
                "plot_test_raw_r2": plot_r2,
                "plot_dir": str(solution.relative_to(GALLERY)),
                "comparison_png": str((solution / "comparison.png").relative_to(GALLERY)),
                "comparison_pdf": str((solution / "comparison.pdf").relative_to(GALLERY)),
            }
            rows.append(record)
            task_rows.append(record)

        cells = []
        for record in task_rows:
            score = f"official {record['official_reward']:.6g}"
            plot_score = "plot test R2 n/a" if record["plot_test_raw_r2"] is None else f"plot test R2 {float(record['plot_test_raw_r2']):.6g}"
            image = html.escape(record["comparison_png"])
            pdf = html.escape(record["comparison_pdf"])
            label = html.escape(record["run"])
            status = html.escape(record["plot_status"])
            cells.append(
                f'<td><a href="{pdf}"><img src="{image}" loading="lazy" alt="{label}"></a>'
                f'<div><b>{label}</b><br>{score}<br>{plot_score}<br>{status}</div></td>'
            )
    csv_path = GALLERY / "score_table.csv"
    fieldnames = ["task", "run", "trial", "official_reward", "plot_status", "plot_test_raw_r2", "plot_dir", "comparison_png", "comparison_pdf"]
    with csv_path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    by_task = {}
    for record in rows:
        by_task.setdefault(record["task"], []).append(record)
    body_rows = []
    for task in sorted(by_task, key=lambda name: task_key(pathlib.Path(name))):
        records = sorted(by_task[task], key=lambda item: int(item["run"].split("_")[1]))
        cells = []
        for record in records:
            score = f"official {record['official_reward']:.6g}"
            plot_score = "plot test R2 n/a" if record["plot_test_raw_r2"] is None else f"plot test R2 {float(record['plot_test_raw_r2']):.6g}"
            image = html.escape(record["comparison_png"])
            pdf = html.escape(record["comparison_pdf"])
            label = html.escape(record["run"])
            status = html.escape(record["plot_status"])
            solution = GALLERY / record["plot_dir"]
            supplemental = []
            for name in ("highdim.png", "spatial.png"):
                if (solution / name).exists():
                    link = html.escape(str(pathlib.Path(record["plot_dir"]) / name))
                    supplemental.append(f'<a href="{link}">{name[:-4]}</a>')
            extra = f'<br>{" · ".join(supplemental)}' if supplemental else ""
            cells.append(
                f'<td><a href="{pdf}"><img src="{image}" loading="lazy" alt="{label}"></a>'
                f'<div><b>{label}</b><br>{score}<br>{plot_score}<br>{status}{extra}</div></td>'
            )
        body_rows.append(f'<tr><th>{html.escape(task)}</th>{"".join(cells)}</tr>')

    ok = sum(record["plot_status"] == "ok" for record in rows)
    failed = len(rows) - ok
    document = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>gpt-5.6-sol: 55 tasks x 3 runs</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 24px; color: #172033; background: #f7f8fb; }}
h1 {{ margin-bottom: 6px; }}
.note {{ color: #4b5563; margin-bottom: 18px; }}
table {{ border-collapse: separate; border-spacing: 10px; width: 100%; table-layout: fixed; }}
th {{ width: 100px; vertical-align: top; text-align: left; padding-top: 12px; }}
td {{ background: white; border: 1px solid #d7dce5; border-radius: 6px; padding: 8px; vertical-align: top; font-size: 12px; line-height: 1.45; }}
td img {{ display: block; width: 100%; height: 190px; object-fit: contain; background: #fff; border-bottom: 1px solid #edf0f4; margin-bottom: 6px; }}
a {{ color: inherit; text-decoration: none; }}
tr {{ page-break-inside: avoid; }}
.fail {{ color: #b91c1c; }}
</style></head><body>
<h1>gpt-5.6-sol: 55 tasks x 3 runs</h1>
<div class="note">{len(by_task)} tasks, {len(rows)} run-level plots. Click an image to open the PDF. Official reward is the recorded evaluator score; plot test R2 is recomputed from the packaged split. {ok} successful plot runs, {failed} explicit failure placeholders.</div>
<table><thead><tr><th>Task</th><th>Run 01</th><th>Run 02</th><th>Run 03</th></tr></thead>
<tbody>{''.join(body_rows)}</tbody></table>
</body></html>'''
    (GALLERY / "index.html").write_text(document)

    readme = f'''# gpt-5.6-sol plot gallery

This directory contains the complete 55-task x 3-run comparison gallery ({len(rows)} run-level outputs).

- Open `index.html` for the three side-by-side plots for every task.
- `score_table.csv` contains the recorded official reward and recomputed plot metrics.
- Each run directory contains `comparison.png`, `comparison.pdf`, `predictions.csv`, and `metrics.json`.
- Two original submissions had no `law.py` and official reward -1; their red placeholder figures explicitly mark the missing submission rather than inventing a curve.
'''
    (GALLERY / "README.md").write_text(readme)
    print(f"indexed {len(by_task)} tasks and {len(rows)} runs ({ok} successful, {failed} placeholders)")


if __name__ == "__main__":
    main()
