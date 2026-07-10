"""Red-first parity/domain-invariant gates.

Runs the checker scripts against:
  * tests/contracts/aligned/            -> must be green (exit 0, no findings)
  * tests/contracts/pre-reconciliation/ -> must be red, with the EXACT finding
    IDs pinned by tests/contracts/expected-red-manifest.json (frozen; identity
    rules excluded).

The harness itself exits 0 when the checkers behave exactly as expected, even
though the direct target checks are red — that is the point of red-first.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent
MANIFEST = json.loads((FIXTURES / "expected-red-manifest.json").read_text(encoding="utf-8"))

PARITY = REPO_ROOT / "scripts" / "check_contract_parity.py"
INVARIANTS = REPO_ROOT / "scripts" / "check_domain_invariants.py"

BLOCKING_SEVERITIES = {"critical", "high", "medium"}


def run_checker(script: Path, *args: str) -> tuple[int, dict]:
    proc = subprocess.run(
        ["uv", "run", str(script), "--format", "json", *args],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert proc.stdout, f"{script.name} produced no output: {proc.stderr}"
    return proc.returncode, json.loads(proc.stdout)


def expected_ids(check: str) -> list[str]:
    return [f["id"] for f in MANIFEST["checks"][check]["expected_findings"]]


def expected_severities(check: str) -> dict[str, str]:
    return {f["id"]: f["severity"] for f in MANIFEST["checks"][check]["expected_findings"]}


class TestManifest:
    def test_severity_enum_is_frozen(self) -> None:
        assert MANIFEST["severity_enum"] == ["critical", "high", "medium", "low", "info"]

    def test_identity_rules_are_excluded(self) -> None:
        assert "identity" in MANIFEST["excluded_rule_classes"]
        for check in MANIFEST["checks"].values():
            for f in check["expected_findings"]:
                assert "IDN" not in f["id"], "identity rules must not be in the manifest"

    def test_manifest_severities_are_valid(self) -> None:
        enum = set(MANIFEST["severity_enum"])
        for check in MANIFEST["checks"].values():
            for f in check["expected_findings"]:
                assert f["severity"] in enum


class TestAlignedGreen:
    def test_parity_green(self) -> None:
        code, report = run_checker(
            PARITY, "--root", str(FIXTURES / "aligned" / "contracts")
        )
        assert code == 0, report
        assert report["status"] == "green"
        assert report["findings"] == []

    def test_invariants_green(self) -> None:
        code, report = run_checker(
            INVARIANTS, "--entities", str(FIXTURES / "aligned" / "entities")
        )
        assert code == 0, report
        assert report["status"] == "green"
        assert report["findings"] == []


class TestPreReconciliationExpectedRed:
    def test_parity_red_exact_ids(self) -> None:
        code, report = run_checker(
            PARITY, "--root", str(FIXTURES / "pre-reconciliation" / "contracts")
        )
        assert code == 1, "pre-reconciliation parity must be red"
        got = [f["id"] for f in report["findings"]]
        assert got == expected_ids("contract-parity")
        sev = expected_severities("contract-parity")
        for f in report["findings"]:
            assert f["severity"] == sev[f["id"]]

    def test_invariants_red_exact_ids(self) -> None:
        code, report = run_checker(
            INVARIANTS, "--entities", str(FIXTURES / "pre-reconciliation" / "entities")
        )
        assert code == 1, "pre-reconciliation invariants must be red"
        non_identity = [f for f in report["findings"] if f["rule_class"] != "identity"]
        got = sorted({f["id"] for f in non_identity})
        assert got == sorted(expected_ids("domain-invariants"))
        sev = expected_severities("domain-invariants")
        for f in non_identity:
            assert f["severity"] == sev[f["id"]]

    def test_identity_findings_present_but_never_blocking(self) -> None:
        code, report = run_checker(
            INVARIANTS, "--entities", str(FIXTURES / "pre-reconciliation" / "entities")
        )
        identity = [f for f in report["findings"] if f["rule_class"] == "identity"]
        assert [f["id"] for f in identity] == ["PIBRAS-IDN-001"]
        blocking_non_identity = [
            f
            for f in report["findings"]
            if f["severity"] in BLOCKING_SEVERITIES and f["rule_class"] != "identity"
        ]
        assert report["blocking_count"] == len(blocking_non_identity)


class TestRealContractsExpectedRed:
    """Direct target checks against the real repo contracts: expected red."""

    def test_real_parity_is_red_with_known_ids(self) -> None:
        code, report = run_checker(PARITY, "--root", str(REPO_ROOT))
        assert code == 1, "real contracts are expected red until reconciled"
        got = [f["id"] for f in report["findings"]]
        assert got == expected_ids("contract-parity")


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
