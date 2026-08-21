"""Release-policy gate tests.

The approved plan states that `rfc_accepted` "requires two maintainer
approvals" and that acceptance must record "immutable review references".
Neither was enforced by schema/release-policy.schema.json: a single approval
with no reference validated cleanly, so the governance gate was weaker than
the documentation describing it.

These tests pin the documented rule to the executable one.
"""

from __future__ import annotations

import copy
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


class TestRfcAcceptedRequiresTwoMaintainers:
    """The documented two-approver rule must be machine-enforced."""

    def test_single_rfc_approval_is_rejected(self) -> None:
        policy = base_policy("rfc_accepted", [identity_approval(), rfc_approval("alice")])
        assert errors(policy), (
            "one rfc approval must not satisfy rfc_accepted; the plan requires two "
            "maintainer approvals"
        )

    def test_two_rfc_approvals_are_accepted(self) -> None:
        policy = base_policy(
            "rfc_accepted",
            [identity_approval(), rfc_approval("alice"), rfc_approval("bob")],
        )
        assert errors(policy) == []

    def test_two_approvals_by_the_same_person_are_rejected(self, tmp_path) -> None:
        # Distinctness cannot be expressed in JSON Schema (uniqueItems compares
        # whole items, and these differ by review_reference), so the rule lives
        # in the validator and is exercised through its CLI.
        duplicate = rfc_approval("alice")
        policy = base_policy(
            "rfc_accepted", [identity_approval(), duplicate, copy.deepcopy(duplicate)]
        )
        assert errors(policy) == [], "schema alone cannot catch this"
        assert run_validator(policy, tmp_path) != 0, "the same approver must not count twice"

    def test_two_distinct_approvers_pass_the_validator(self, tmp_path) -> None:
        policy = base_policy(
            "rfc_accepted",
            [identity_approval(), rfc_approval("alice"), rfc_approval("bob")],
        )
        assert run_validator(policy, tmp_path) == 0

    def test_rfc_approval_requires_a_review_reference(self) -> None:
        without_reference = rfc_approval("alice")
        del without_reference["review_reference"]
        policy = base_policy(
            "rfc_accepted", [identity_approval(), without_reference, rfc_approval("bob")]
        )
        assert errors(policy), "the plan requires immutable review references"

    def test_earlier_phase_approval_is_still_required(self) -> None:
        policy = base_policy("rfc_accepted", [rfc_approval("alice"), rfc_approval("bob")])
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
def test_later_phases_still_require_two_rfc_approvals(phase: str) -> None:
    """Phases beyond rfc_accepted inherit its requirements."""
    policy = base_policy(
        phase, [identity_approval(), rfc_approval("alice"), rfc_approval("bob")]
    )
    single = base_policy(phase, [identity_approval(), rfc_approval("alice")])
    assert len(errors(single)) >= len(errors(policy))
