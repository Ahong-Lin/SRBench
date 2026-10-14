"""Standalone Harbor verifier; imports the same row runner and metrics as plotting."""
import json
import os
import secrets
from pathlib import Path
import pandas as pd
from prediction import isolated_predictions
from metrics import regression_metrics


def evaluate(law_path, data_path, contract_path, log_dir, *, drop_privileges=True):
    law_path, data_path = Path(law_path), Path(data_path)
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    stash = None
    try:
        contract = json.loads(Path(contract_path).read_text(encoding="utf-8"))
        frame = pd.read_csv(data_path)
        rows = frame[contract["features"]].to_dict(orient="records")
        labels = frame[contract["target"]].to_numpy(dtype=float)
        # Only the verifier keeps the labels. Candidate code runs as nobody
        # inside Harbor and cannot read this root-owned temporary file.
        stash = data_path.with_name("." + data_path.name + "." + secrets.token_hex(12))
        mode = data_path.stat().st_mode & 0o777
        os.replace(data_path, stash)
        os.chmod(stash, 0o600)
        result = isolated_predictions(law_path, rows, contract["target"], seed=None,
                                      drop_privileges=drop_privileges)
        if not result.ok:
            raise RuntimeError(result.errors[0]["error"])
        report = regression_metrics(result.values, labels)
        if report["status"] != "ok":
            raise ValueError("hidden target variation is too small for R²")
    except Exception as exc:
        report = {"status": "evaluation_failed", "error": f"{type(exc).__name__}: {exc}", "raw_r2": None}
        (log_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        (log_dir / "reward.txt").write_text("-1.000000\n", encoding="utf-8")
        print(json.dumps(report))
        return 1
    finally:
        if stash is not None and stash.exists():
            os.replace(stash, data_path)
            os.chmod(data_path, mode)
    (log_dir / "metrics.json").write_text(json.dumps(report, allow_nan=False, indent=2), encoding="utf-8")
    (log_dir / "reward.txt").write_text(f"{report['raw_r2']:.6f}\n", encoding="utf-8")
    print(json.dumps(report, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(evaluate("/app/law.py", "/tests/test_data.csv",
                             "/tests/contract.json", "/logs/verifier"))

