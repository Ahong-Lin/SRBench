"""Create explicit placeholders for submissions that never produced law.py."""

from __future__ import annotations

import csv
import json
import pathlib

import matplotlib.pyplot as plt


ROOT = pathlib.Path("outputs/bio_phys_30_gpt56sol_20260921")
PLOT = ROOT / "03_plots/LLM_vs_truth_20260922/gpt56sol_20260922_55x3"
EVAL = ROOT / "04_evaluations/gpt56sol_20260922_55x3"
PACK = ROOT / "02_packaged/20260922"
FAILED = [
    ("biology_009", "run_01_task__LxPYuqB", "task__LxPYuqB"),
    ("biology_013", "run_01_task__TX4WA8k", "task__TX4WA8k"),
]


def main() -> None:
    for task, run, trial in FAILED:
        folder = PLOT / task / "solutions" / run
        folder.mkdir(parents=True, exist_ok=True)
        result = json.loads((EVAL / trial / "result.json").read_text())
        reward = result["verifier_result"]["rewards"]["reward"]
        train_rows = sum(1 for _ in (PACK / task / "task/environment/train_data.csv").open()) - 1
        test_rows = sum(1 for _ in (PACK / task / "task/tests/test_data.csv").open()) - 1

        fig, ax = plt.subplots(figsize=(10, 5.5))
        ax.set_facecolor("#fff5f5")
        ax.text(0.5, 0.69, f"{task} | {run.split('_task__', 1)[0]}",
                ha="center", va="center", fontsize=19, weight="bold", color="#7f1d1d")
        ax.text(0.5, 0.49, "NO SUBMITTED LAW", ha="center", va="center",
                fontsize=18, color="#b91c1c")
        ax.text(0.5, 0.30,
                f"Official reward: {float(reward):.6g}    train: {train_rows}    test: {test_rows}",
                ha="center", va="center", fontsize=11, color="#374151")
        ax.text(0.5, 0.16,
                "The original evaluation recorded no law.py; no prediction curve is fabricated.",
                ha="center", va="center", fontsize=10, color="#4b5563")
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color("#fca5a5")
            spine.set_linewidth(1.5)
        fig.tight_layout()
        fig.savefig(folder / "comparison.png", dpi=180, bbox_inches="tight")
        fig.savefig(folder / "comparison.pdf", bbox_inches="tight")
        plt.close(fig)

        with (folder / "predictions.csv").open("w", newline="") as stream:
            writer = csv.writer(stream)
            writer.writerow(["status", "reason"])
            writer.writerow(["submission_failed", "no law.py in original evaluation"])
        report = {
            "status": "submission_failed",
            "task_id": task,
            "trial": trial,
            "official_reward": reward,
            "n_requested": train_rows + test_rows,
            "n_evaluated": 0,
            "reason": "No law.py was submitted in the original evaluation; placeholder only.",
        }
        (folder / "metrics.json").write_text(json.dumps(report, indent=2))
    print(f"wrote {len(FAILED)} explicit failure placeholders")


if __name__ == "__main__":
    main()
