"""A single-sided mutation must fail on the exact row and representation."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def run(root):
    command = [sys.executable, str(ROOT / "scripts/check_semantic_parity.py"), "--root", str(root)]
    proc = subprocess.run(command, capture_output=True, text=True)
    assert proc.stdout, proc.stderr
    return proc.returncode, json.loads(proc.stdout)


def test_runtime_matrix():
    code, report = run(ROOT)
    assert code == 0 and report["status"] == "green", report


def test_fractional_money_schema_only_mutation(tmp_path):
    (tmp_path / "types").symlink_to(ROOT / "types", target_is_directory=True)
    (tmp_path / "schema").mkdir()
    schema_file = Path("schema/mbras.schema.json")
    schema = json.loads((ROOT / schema_file).read_text())
    schema["$defs"]["Money"]["properties"]["amount"]["type"] = "number"
    (tmp_path / schema_file).write_text(json.dumps(schema))
    code, report = run(tmp_path)
    assert code == 1 and report["status"] == "red", report
    assert [row for row in report["rows"] if row["errors"]] == [
        {"id": "money.fractional", "expected": False, "json_schema": True,
         "zod": False, "errors": ["json_schema.acceptance"]}
    ]


def test_known_observation_is_separate_and_changes_require_review(tmp_path):
    (tmp_path / "types").symlink_to(ROOT / "types", target_is_directory=True)
    (tmp_path / "schema").mkdir()
    path = Path("schema/mbras.schema.json")
    schema = json.loads((ROOT / path).read_text())
    schema["$defs"]["Money"]["properties"]["amount"]["maximum"] = 9007199254740991
    (tmp_path / path).write_text(json.dumps(schema))
    code, report = run(tmp_path)
    assert code == 1 and not any(row["errors"] for row in report["rows"])
    by_id = {row["id"]: row for row in report["compatibility_observations"]}
    assert by_id["money.above-safe-range"]["errors"] == ["json_schema.acceptance"]
    assert by_id["money.below-safe-range"]["errors"] == []
