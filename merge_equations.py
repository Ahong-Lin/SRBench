"""Merge per-subject Stage-3 equation JSONL files into one benchmark index."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


def _load(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"Invalid JSON in {path}:{line_no}: {exc}") from exc
            if not isinstance(value, dict):
                raise SystemExit(f"Expected an object in {path}:{line_no}")
            rows.append(value)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge physics, biology, AI, or other equation JSONL outputs."
    )
    parser.add_argument("--input", nargs="+", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    merged: list[dict] = []
    seen: set[str] = set()
    for path in args.input:
        if not path.exists():
            raise SystemExit(f"Input file not found: {path}")
        for row in _load(path):
            record_id = row.get("scenario_id") or row.get("id")
            if not isinstance(record_id, str) or not record_id:
                raise SystemExit(f"Missing scenario_id/id in {path}")
            if record_id in seen:
                raise SystemExit(f"Duplicate equation id across inputs: {record_id}")
            seen.add(record_id)
            if "scenario_id" not in row:
                row["scenario_id"] = record_id
            merged.append(row)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for row in merged:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    counts = Counter(str(row.get("discipline", "unknown")) for row in merged)
    manifest = args.output.with_name("merge_manifest.json")
    manifest.write_text(
        json.dumps({
            "output": str(args.output),
            "inputs": [str(path) for path in args.input],
            "n_equations": len(merged),
            "counts_by_discipline": dict(sorted(counts.items())),
            "scenario_ids_unique": True,
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Merged {len(merged)} equations into {args.output}")
    print(f"Manifest: {manifest}")


if __name__ == "__main__":
    main()
