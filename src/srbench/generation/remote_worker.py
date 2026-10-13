"""Bootstrap inside a fresh Daytona sandbox; uses only stdlib until install."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def main():
    payload_path = Path(sys.argv[1])
    root = payload_path.parent
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    # Each sandbox has its own environment. A prepared snapshot can satisfy
    # these requirements without downloading the scientific dependencies again.
    subprocess.run([sys.executable, "-m", "pip", "install", "--disable-pip-version-check",
                    str(root / "source")], check=True)
    command = payload["command"]
    command[0] = sys.executable
    return subprocess.call(command, cwd=root)


if __name__ == "__main__":
    raise SystemExit(main())
