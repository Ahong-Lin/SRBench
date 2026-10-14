"""Verify the frozen replay files after cloning; no model or cloud calls."""

import hashlib
import json
from pathlib import Path
import sys


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "evaluation/replay_bundle_manifest.json").read_text())
    errors = []
    for entry in manifest["files"]:
        path = root / entry["path"]
        if entry["type"] == "symlink":
            if not path.is_symlink():
                errors.append(f"Missing symlink: {entry['path']}")
            elif path.readlink().as_posix() != entry["target"] or not path.exists():
                errors.append(f"Invalid symlink: {entry['path']}")
        elif not path.is_file() or path.is_symlink():
            errors.append(f"Missing file: {entry['path']}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            errors.append(f"SHA256 mismatch: {entry['path']}")
    for run in manifest["replays"]:
        dataset = root / run["dataset_path"]
        actual = sorted(path.name for path in dataset.iterdir() if path.is_dir()) if dataset.is_dir() else []
        if actual != run["packaged_task_ids"]:
            errors.append(f"Task inventory mismatch: {run['run_name']}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    count = sum(len(run["packaged_task_ids"]) for run in manifest["replays"])
    print(f"OK: {len(manifest['files'])} files/symlinks; {count} Harbor tasks; SHA256 and links verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
