"""Date-based destinations for truth inspection and model comparisons."""
from datetime import datetime
from pathlib import Path


def plot_directory(root, *, comparison=False):
    prefix = "LLM_vs_truth" if comparison else "solution"
    return Path(root) / "03_plots" / f"{prefix}_{datetime.now():%Y%m%d}"


def comparison_directory(package, task_id):
    package = Path(package).resolve()
    packaged = next((p for p in package.parents if p.name == "02_packaged"), None)
    root = packaged.parent if packaged is not None else package.parent
    return plot_directory(root, comparison=True) / task_id
