"""Release-policy gate tests.

The plan requires that `rfc_accepted` record an approval with an "immutable
review reference". That was not enforced by
schema/release-policy.schema.json: an rfc-gate entry with no reference
validated cleanly, so the governance gate was weaker than the documentation
describing it.

While the project has a single maintainer, the gate is one reviewable
approval — not a count of distinct approvers. These tests pin the documented
rule to the executable one.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schema" / "release-policy.schema.json"
POLICY_PATH = ROOT / "governance" / "release-policy.yaml"


def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validator() -> Draft202012Validator:
    return Draft202012Validator(schema())


def identity_approval() -> dict:
    return {
        "gate": "identity",
        "approver": "Ronaldo",
        "date": "2026-07-10",
        "evidence": "session approval",
    }


def rfc_approval(approver: str) -> dict:
    return {
        "gate": "rfc",
        "approver": approver,
        "date": "2026-08-21",
        "review_reference": f"https://github.com/pibras/pibras/pull/7#{approver}",
    }


def base_policy(phase: str, approvals: list[dict]) -> dict:
    return {
        "policy_version": "0.1.0",
        "phase": phase,
        "identity": {
            "neutral_org": "pibras",
            "canonical_host": "pibras.ibvi.ai",
            "repo_url": "https://github.com/pibras/pibras.git",
            "brand_exempt_paths": ["docs/REVIEW.md"],
        },
        "approvals": approvals,
    }


def run_validator(document: dict, tmp_path: Path) -> int:
    """Run the real validator CLI against a candidate policy."""
    import yaml

    policy_file = tmp_path / "release-policy.yaml"
    policy_file.write_text(yaml.safe_dump(document), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_release_policy.py"), str(policy_file)],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    return result.returncode


def errors(document: dict) -> list[str]:
    return [e.message for e in validator().iter_errors(document)]


class TestRfcAcceptedRequiresApprovalWithReference:
    """The documented approval rule must be machine-enforced.

    While PIBRAS has a single maintainer, the gate is one rfc approval with
    an immutable review reference — not a count of distinct approvers. The
    gate's value is reviewability (a URL a third party can check), not
    headcount.
    """

    def test_rfc_approval_is_accepted(self, tmp_path) -> None:
        policy = base_policy("rfc_accepted", [identity_approval(), rfc_approval("alice")])
        assert errors(policy) == []
        assert run_validator(policy, tmp_path) == 0

    def test_missing_rfc_approval_is_rejected(self) -> None:
        policy = base_policy("rfc_accepted", [identity_approval()])
        assert errors(policy), (
            "rfc_accepted must not be reachable without any rfc-gate approval"
        )

    def test_rfc_approval_requires_a_review_reference(self) -> None:
        without_reference = rfc_approval("alice")
        del without_reference["review_reference"]
        policy = base_policy("rfc_accepted", [identity_approval(), without_reference])
        assert errors(policy), "the plan requires immutable review references"

    def test_review_reference_must_be_nonempty(self) -> None:
        empty_reference = rfc_approval("alice")
        empty_reference["review_reference"] = ""
        policy = base_policy("rfc_accepted", [identity_approval(), empty_reference])
        assert errors(policy), "an empty reference is not an immutable reference"

    def test_validator_rejects_approval_without_reference(self, tmp_path) -> None:
        # The schema catches the missing key; the validator's own presence
        # check is exercised through its CLI for defense in depth.
        without_reference = rfc_approval("alice")
        del without_reference["review_reference"]
        policy = base_policy("rfc_accepted", [identity_approval(), without_reference])
        assert run_validator(policy, tmp_path) != 0

    def test_multiple_approvals_are_still_accepted(self, tmp_path) -> None:
        # Nothing forbids more approvers; the gate is a floor, not a ceiling.
        policy = base_policy(
            "rfc_accepted",
            [identity_approval(), rfc_approval("alice"), rfc_approval("bob")],
        )
        assert run_validator(policy, tmp_path) == 0

    def test_earlier_phase_approval_is_still_required(self) -> None:
        policy = base_policy("rfc_accepted", [rfc_approval("alice")])
        assert errors(policy), "rfc_accepted must still carry the identity approval"


class TestIdentityPhaseUnchanged:
    """Hardening rfc_accepted must not break the phase currently in use."""

    def test_current_committed_policy_validates(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_release_policy.py"), str(POLICY_PATH)],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        assert result.returncode == 0, result.stderr or result.stdout

    def test_identity_phase_needs_only_one_identity_approval(self) -> None:
        policy = base_policy("identity", [identity_approval()])
        assert errors(policy) == []


@pytest.mark.parametrize("phase", ["legal_approved", "rc", "final"])
def test_later_phases_inherit_rfc_gate_requirements(phase: str) -> None:
    """Phases beyond rfc_accepted inherit its requirements."""
    complete = base_policy(phase, [identity_approval(), rfc_approval("alice")])
    missing_reference = rfc_approval("alice")
    del missing_reference["review_reference"]
    incomplete = base_policy(phase, [identity_approval(), missing_reference])
    assert len(errors(incomplete)) > len(errors(complete))
