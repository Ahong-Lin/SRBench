"""Package static laws and typed ODE derivative targets as Harbor tasks."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import shutil
import tempfile
from datetime import date
from pathlib import Path
from srbench.common import metrics, prediction
from srbench.common.contracts import contract_from_spec, noiseless_spec
from srbench.common.io import read_json, read_jsonl, write_json, relative_artifact, safe_name
from .reference import reference_source, check_reference_source, truth_values
from .split import build_split
from srbench.generation.response_diagnostics import mechanism_coverage


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _implementation_digest():
    root = Path(__file__).resolve().parents[1]
    sources = [root / name for name in (
        "packaging/pipeline.py", "packaging/split.py", "packaging/reference.py",
        "common/contracts.py", "common/io.py", "common/prediction.py", "common/metrics.py",
        "generation/data_generator.py", "generation/response_diagnostics.py",
        "common/polynomial_equilibrium.py",
    )]
    sources += [p for p in (root / "packaging/template").rglob("*")
                if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    digest = hashlib.sha256()
    for path in sorted(sources):
        digest.update(str(path.relative_to(root)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _harbor_name(task_id):
    slug = re.sub(r"[^A-Za-z0-9_-]+", "-", task_id).strip("-") or "task"
    if slug != task_id:
        slug += "-" + hashlib.sha256(task_id.encode()).hexdigest()[:8]
    return "srbench-v7/" + slug


def _instruction(spec, contract, split):
    template = (Path(__file__).parent / "template/instruction.md").read_text(encoding="utf-8")
    if contract.family == "ode":
        description = f"{contract.target} is the instantaneous time derivative of state {spec['benchmark_target_state']}. Inputs contain time and observed states along a trajectory."
    else:
        description = f"{contract.target} is the response to independently sampled experimental conditions."
    region = "Infer the governing relationship from the supplied training observations. The evaluator independently tests the submitted function on hidden observations."
    axes = {a["symbol"]: a for a in spec["independent_variables"]}
    variables = []
    for name in contract.features:
        if name in axes:
            role = "time" if contract.family == "ode" else "integer-valued independent input" if axes[name].get("type") == "integer" else "independent input"
            variables.append(f"- {name}: {role}.")
        else:
            variables.append(f"- {name}: observed dynamical state; use its value in each input row.")
    for old, new in {
        "{{TARGET_DESCRIPTION}}": description, "{{VARIABLES}}": "\n".join(variables),
        "{{FEATURES}}": ", ".join(contract.features), "{{TARGET}}": contract.target,
        "{{TRAIN_POINTS}}": str(split["train_points"]), "{{TEST_POINTS}}": str(split["test_points"]),
        "{{REGION}}": region,
        "{{LABEL_DESCRIPTION}}": "exact formula outputs without observation noise",
    }.items():
        template = template.replace(old, new)
    return template


def build_package(spec_path, destination, *, n_total=5000, test_points=500, seed=0,
                  task_id=None, train_csv=None, test_csv=None, resume=False):
    spec_path, destination = Path(spec_path).resolve(), Path(destination).resolve()
    task_id = safe_name(task_id or destination.name)
    spec = noiseless_spec(read_json(spec_path))
    contract = contract_from_spec(spec)
    config = {"spec_sha256": _sha(spec_path), "implementation_sha256": _implementation_digest(),
              "n_total": n_total, "test_points": test_points, "seed": seed,
              "label_policy": "clean_ground_truth",
              "train_sha256": _sha(train_csv) if train_csv else None,
              "test_sha256": _sha(test_csv) if test_csv else None}
    if destination.exists():
        manifest_path = destination / "manifest.json"
        if resume and manifest_path.exists():
            previous = read_json(manifest_path)
            if previous.get("build_config") == config and previous.get("task_id") == task_id:
                for relative, digest in previous["file_sha256"].items():
                    if _sha(relative_artifact(destination, relative)) != digest:
                        raise ValueError(f"existing package changed: {relative}; choose a new output path")
                return destination
        raise ValueError(f"package exists or differs from this request: {destination}; use --resume for identical packages")
    train, test, split = build_split(spec, contract, n_total=n_total, test_points=test_points,
                                     seed=seed, train_csv=train_csv, test_csv=test_csv)
    # The official package split is the authoritative coverage audit.  It is a
    # deterministic report and does not affect acceptance or alter the law.
    coverage = mechanism_coverage(spec, train, test)
    spec["coverage_report"] = coverage
    spec["inactive_mechanisms"] = coverage.get("inactive_mechanisms", [])
    spec["target_variance"] = {
        "train": {"n": int(len(train)), "variance": float(train[contract.target].var(ddof=0)),
                  "range": float(train[contract.target].max() - train[contract.target].min())},
        "hidden": {"n": int(len(test)), "variance": float(test[contract.target].var(ddof=0)),
                   "range": float(test[contract.target].max() - test[contract.target].min())},
    }
    source = reference_source(contract)
    oracle = {}
    for label, frame in (("train", train), ("test", test)):
        values = check_reference_source(source, frame, contract)
        oracle[label] = {"versus_clean_truth": metrics.regression_metrics(values, truth_values(contract, frame)),
                         "versus_observed_label": metrics.regression_metrics(values, frame[contract.target])}
    if oracle["test"]["versus_observed_label"]["status"] != "ok":
        raise ValueError("hidden labels have near-zero variance; the existing Harbor R² metric is undefined")
    destination.parent.mkdir(parents=True, exist_ok=True)
    template = Path(__file__).parent / "template"
    with tempfile.TemporaryDirectory(prefix=f".{task_id}-", dir=destination.parent) as temporary:
        stage = Path(temporary) / "package"
        task = stage / "task"
        shutil.copytree(template, task, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        (task / "solution").mkdir()
        train.to_csv(task / "environment/train_data.csv", index=False)
        test.to_csv(task / "tests/test_data.csv", index=False)
        for module in (metrics, prediction):
            shutil.copy2(module.__file__, task / "tests" / Path(module.__file__).name)
        write_json(task / "tests/contract.json", {"features": contract.features, "target": contract.target})
        (task / "solution/reference_law.py").write_text(source, encoding="utf-8")
        (task / "solution/solve.sh").write_text(
            "#!/bin/sh\nset -eu\ncp /solution/reference_law.py /app/law.py\ncp /solution/explain.md /app/explain.md\n",
            encoding="utf-8")
        (task / "solution/solve.sh").chmod(0o755)
        (task / "tests/test.sh").chmod(0o755)
        (task / "solution/explain.md").write_text(
            f"Ground truth: {contract.target} = {contract.expression}\n\nFixed parameters: {contract.parameters}\n",
            encoding="utf-8")
        (task / "instruction.md").write_text(_instruction(spec, contract, split), encoding="utf-8")
        task_toml = (task / "task.toml").read_text(encoding="utf-8").replace(
            "{{TAGS}}", json.dumps(["symbolic_regression", "srbench-v7", str(spec.get("discipline") or "science"), contract.family]))
        task_toml = task_toml.replace("{{TASK_NAME}}", json.dumps(_harbor_name(task_id)))
        (task / "task.toml").write_text(task_toml, encoding="utf-8")
        write_json(stage / "ground_truth.json", {"version": 7, "spec": spec, "contract": contract.to_dict()})
        write_json(stage / "split_manifest.json", split)
        paths = {"task": "task", "ground_truth": "ground_truth.json", "split": "split_manifest.json",
                 "train": "task/environment/train_data.csv", "test": "task/tests/test_data.csv",
                 "reference": "task/solution/reference_law.py"}
        manifest = {
            "version": 7, "task_id": task_id, "harbor_name": _harbor_name(task_id),
            "build_config": config, "paths": paths,
            "contract": {"features": contract.features, "target": contract.target, "family": contract.family},
            "oracle_self_test": oracle, "difficulty": "unmeasured", "solver_evaluated": False,
            "coverage": coverage,
            "dimensions": {"static_inputs": len(contract.features) if contract.family == "static" else 0,
                           "ode_states": len(spec.get("state_variables") or []), "row_features": len(contract.features)},
        }
        manifest["file_sha256"] = {str(p.relative_to(stage)): _sha(p) for p in sorted(stage.rglob("*")) if p.is_file()}
        write_json(stage / "manifest.json", manifest)
        stage.rename(destination)
    return destination


def main(argv=None):
    p = argparse.ArgumentParser(prog="srbench package", description=__doc__)
    inputs = p.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--run", help="run name in --outputs-dir, or an existing run directory")
    inputs.add_argument("--spec", type=Path, help="one DataGenSpec JSON")
    inputs.add_argument("--candidate", type=Path, help="one directory under 01_generated")
    p.add_argument("--outputs-dir", type=Path, default=Path("outputs"))
    p.add_argument("--output", type=Path, help="single package destination; with --run, parent for all packages")
    p.add_argument("--task-id", help="single package name")
    p.add_argument("--n-total", type=int, default=5000)
    p.add_argument("--test-points", type=int, default=500)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--train-csv", type=Path)
    p.add_argument("--test-csv", type=Path)
    p.add_argument("--resume", action="store_true")
    args = p.parse_args(argv)
    jobs = []
    if args.run:
        if args.task_id or args.train_csv or args.test_csv:
            p.error("--task-id and provided CSVs apply only to a single package")
        run = Path(args.run)
        if not run.is_dir():
            run = args.outputs_dir / safe_name(args.run)
        run = run.resolve()
        index = read_jsonl(run / "01_generated/index.jsonl")
        if not index:
            p.error(f"no accepted candidates: {run / '01_generated/index.jsonl'}")
        output = args.output or run / "02_packaged" / date.today().strftime("%Y%m%d")
        for i, entry in enumerate(index):
            task_id = safe_name(entry["candidate_id"])
            jobs.append((relative_artifact(run, entry["spec"]), output / task_id, task_id, args.seed + i))
    else:
        spec = args.spec or args.candidate / "spec.json"
        default_id = args.task_id or (args.candidate.name if args.candidate else (spec.parent.name or spec.stem))
        output = args.output or args.outputs_dir / "manual/02_packaged" / safe_name(default_id)
        jobs.append((spec, output, args.task_id or output.name, args.seed))
    for spec, destination, task_id, seed in jobs:
        result = build_package(spec, destination, n_total=args.n_total, test_points=args.test_points,
                               seed=seed, task_id=task_id, train_csv=args.train_csv, test_csv=args.test_csv, resume=args.resume)
        print(result, flush=True)
    if args.run:
        dataset = output / "harbor_dataset"
        dataset.mkdir(exist_ok=True)
        for _, destination, task_id, _ in jobs:
            link = dataset / task_id
            target = (destination / "task").resolve()
            if link.exists() or link.is_symlink():
                if not link.is_symlink() or link.resolve() != target:
                    raise ValueError(f"unrelated entry in Harbor dataset: {link}")
            else:
                link.symlink_to(os.path.relpath(target, dataset.resolve()), target_is_directory=True)
        print(f"Harbor dataset: {dataset}", flush=True)


if __name__ == "__main__":
    main()
