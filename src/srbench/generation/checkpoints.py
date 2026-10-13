"""Locate one job's checkpoints without depending on filename time zones."""
from pathlib import Path

from srbench.common.io import read_jsonl


def latest_run(output: Path) -> Path | None:
    runs = [path for path in output.glob("candidate_*") if path.is_dir()]
    return max(runs, key=lambda path: (path.stat().st_mtime_ns, path.name), default=None)


def attempt_outcomes(run: Path) -> dict[int, dict]:
    # A resumed attempt may have an earlier service failure followed by success.
    return {item.get("attempt", index): item
            for index, item in enumerate(read_jsonl(run / "lineage_attempts.jsonl"), 1)}


def candidate_failure(run: Path) -> dict | None:
    """Recognize a scenario's numeric failure, including the old finite-data check.

    Deliberately match only that exact legacy error. Arbitrary ValueErrors,
    service errors and missing/corrupt artifacts must still stop the batch.
    """
    outcomes = attempt_outcomes(run)
    failure = outcomes[max(outcomes)] if outcomes else {}
    if failure.get("status") == "candidate_error":
        return dict(failure)
    if (failure.get("status") == "pipeline_error" and failure.get("error") ==
            "ValueError: candidate data has wrong row count or nonfinite values"):
        return failure | {"status": "candidate_error", "legacy_status": "pipeline_error",
                          "failure_kind": "invalid_numeric_data"}
    return None
