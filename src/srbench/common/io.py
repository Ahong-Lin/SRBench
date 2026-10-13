"""Small, deterministic artifact helpers shared by the three stages."""
import json
from pathlib import Path


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_jsonl(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []


def append_jsonl(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")


def safe_name(name):
    if not name or Path(name).name != name or name in {".", ".."}:
        raise ValueError("name must be one non-empty directory name")
    return name


def relative_artifact(root, name):
    """Resolve an artifact within a relocatable manifest's directory."""
    root = Path(root).resolve()
    result = (root / name).resolve()
    if not result.is_relative_to(root):
        raise ValueError(f"artifact escapes package directory: {name}")
    return result
