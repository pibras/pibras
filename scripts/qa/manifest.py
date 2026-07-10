#!/usr/bin/env python3
"""Write a QA evidence manifest. Usage: manifest.py <report-path> <status> <todo-id> <artifact>..."""
import datetime
import hashlib
import json
import os
import subprocess
import sys


def sha(p: str) -> str:
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main() -> int:
    report, status, todo_id, *paths = sys.argv[1:]
    manifest = {
        "todo_id": int(todo_id),
        "status": status,
        "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True
        ).stdout.strip(),
        "artifacts": [{"path": p, "sha256": sha(p), "bundle": True} for p in paths],
    }
    os.makedirs(os.path.dirname(report) or ".", exist_ok=True)
    with open(report, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"manifest written: {report} (status={status})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
