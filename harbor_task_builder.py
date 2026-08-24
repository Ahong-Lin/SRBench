"""Export generated SRBench data as a self-contained Harbor task directory.

The exporter copies a user-supplied, already working Harbor task as its
environment/template and replaces only the task-specific train/test data,
instruction, and verifier feature/target configuration.  It does not expose
the equation or parameters to the agent.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


def _load_spec(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("spec JSON must contain one object")
    return value


def _safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "srbench_task"


def _replace_task_config(source: str, features: list[str], target: str) -> str:
    source = re.sub(r"^FEATURE_NAMES\s*=.*$", f"FEATURE_NAMES = {features!r}", source,
                    flags=re.MULTILINE)
    source = re.sub(r"^TARGET_NAME\s*=.*$", f"TARGET_NAME = {target!r}", source,
                    flags=re.MULTILINE)
    if "FEATURE_NAMES" not in source or "TARGET_NAME" not in source:
        raise ValueError("template verifier must define FEATURE_NAMES and TARGET_NAME")
    return source


def _instruction(spec: dict[str, Any], features: list[str], target: str) -> str:
    discipline = str(spec.get("discipline") or "science")
    scenario = str(spec.get("scenario_text") or "an experimental system")
    columns = "\n".join(f"- `{name}`: input variable" for name in features)
    return f"""You have to analyze an experimental dataset to discover the underlying mathematical relationship that governs it.
The training dataset is located at `/app/data/train_data.csv` and can be loaded using `pandas.read_csv()`.

The experimental context: This is a symbolic regression task from the {discipline} domain. {scenario}
The goal is to discover a closed-form mathematical expression that predicts `{target}` from the observed input variables.

The dataset columns are:
{columns}
- `{target}`: output variable (the value you must predict)

You must produce two files:

1. A Python function in `/app/law.py` named `law` with this signature:

```python
def law(input_data: list[dict[str, float]]) -> list[dict[str, float]]:
    # Return one {{"{target}": prediction}} dict per input row.
    pass
```

2. A detailed explanation in `/app/explain.md` describing the discovered formula,
methodology, and fitted parameters.

Your submitted `law` function will be tested on a hidden, independently generated dataset.
"""


def build_task(template: Path, train_csv: Path, test_csv: Path, spec_path: Path,
               output_dir: Path, name: str | None = None) -> Path:
    if not template.is_dir():
        raise ValueError(f"Harbor template directory does not exist: {template}")
    for required in ("environment/Dockerfile", "tests/test_outputs.py", "task.toml"):
        if not (template / required).exists():
            raise ValueError(f"template misses required Harbor file: {required}")
    spec = _load_spec(spec_path)
    train = pd.read_csv(train_csv)
    test = pd.read_csv(test_csv)
    target = str(spec.get("benchmark_output") or spec.get("dependent_variable") or "y")
    if target not in train.columns or target not in test.columns:
        raise ValueError(f"target '{target}' is absent from train or test CSV")
    # Never infer features by taking "all non-target CSV columns": generators
    # may include an optional ``<target>_noisy`` diagnostic column, which would
    # leak the label to the solver.  The spec is authoritative.  For an ODE,
    # state values plus time are legitimate observed covariates for the selected
    # derivative/RHS target; for a static law only its independent axes are.
    features = [str(item["symbol"]) for item in spec.get("independent_variables", [])]
    if spec.get("integrator") == "integrate_system":
        for item in spec.get("state_variables", []):
            features.append(str(item["symbol"]) if isinstance(item, dict) else str(item))
    features = list(dict.fromkeys(features))
    missing = [column for column in features if column not in train.columns]
    if missing:
        raise ValueError("spec-declared feature columns absent from CSV: " + ", ".join(missing))
    if not features or list(test.columns) != list(train.columns):
        raise ValueError("train/test CSVs need matching columns and at least one feature")
    task_dir = output_dir / _safe_name(name or f"{spec.get('record_id', 'srbench')}_gen{spec.get('generation', '?')}")
    if task_dir.exists():
        raise ValueError(f"refusing to overwrite existing task directory: {task_dir}")
    shutil.copytree(template, task_dir, ignore=shutil.ignore_patterns("solution", "jobs", "artifacts", "*.pyc", "__pycache__"))
    (task_dir / "environment").mkdir(exist_ok=True)
    (task_dir / "tests").mkdir(exist_ok=True)
    shutil.copy2(train_csv, task_dir / "environment" / "train_data.csv")
    shutil.copy2(test_csv, task_dir / "tests" / "test_data.csv")
    verifier = (task_dir / "tests" / "test_outputs.py")
    verifier.write_text(_replace_task_config(verifier.read_text(encoding="utf-8"), features, target), encoding="utf-8")
    (task_dir / "instruction.md").write_text(_instruction(spec, features, target), encoding="utf-8")
    (task_dir / "srbench_manifest.json").write_text(json.dumps({
        "source_spec": str(spec_path.resolve()), "source_train_csv": str(train_csv.resolve()),
        "source_hidden_test_csv": str(test_csv.resolve()), "features": features, "target": target,
        "metric": "raw test R² = 1 - MSE / Var(y_test); reporting uses clip(raw, -1, 1)",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return task_dir


def main() -> None:
    p = argparse.ArgumentParser(description="Build a Harbor-format SR task from generated train/test CSVs.")
    p.add_argument("--template", required=True, type=Path, help="a known-good Harbor task directory")
    p.add_argument("--train", required=True, type=Path)
    p.add_argument("--test", required=True, type=Path)
    p.add_argument("--spec", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    p.add_argument("--name", default=None)
    args = p.parse_args()
    print(build_task(args.template, args.train, args.test, args.spec, args.output_dir, args.name))


if __name__ == "__main__":
    main()
