"""Privacy channel gates.

Traces privacy decisions to what each output channel can actually emit, using
only synthetic fixtures from tests/golden/. Every condition exercised here is
mapped to its normative source and fixture in docs/privacy-verification.md,
and test_verification_doc_matches_fixtures keeps that map honest.

What this file proves, and what it does not:

* It proves that the executable controls in this repository (the reference
  policy evaluator in scripts/validate_conformance.py, the schema.org exporter,
  the property_public view text, the feed validator and the JSON Schema) behave
  as the fixtures declare, and that each control fails when its protected
  property is removed (the mutation-style tests).
* It does not prove operator obligations (privacy notice, contracts in force,
  incident response, real DSAR deadlines). Those are listed as operator
  obligations in docs/privacy-verification.md.
* Fulfilled DSAR records must carry evidence and a concrete effect.
"""

from __future__ import annotations

import copy
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import export_schema_org as schema_org  # noqa: E402
from scripts import validate_conformance as conformance  # noqa: E402

GOLDEN = ROOT / "tests" / "golden"
SCHEMA_PATH = ROOT / "schema" / "mbras.schema.json"
DDL_PATH = ROOT / "db" / "schema.sql"
CASES_PATH = GOLDEN / "conformance-cases.json"
DOC_PATH = ROOT / "docs" / "privacy-verification.md"

SCHEMA: dict[str, Any] = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
ROOT_VALIDATOR = Draft202012Validator(
    SCHEMA, format_checker=Draft202012Validator.FORMAT_CHECKER
)

# Every fixture this suite (or the verification doc) relies on. The doc must
# mention each one; the conformance index must register each one.
PRIVACY_FIXTURES = (
    "exposure-policy.default-deny.json",
    "listing.public-masked.json",
    "portal-feed.valid.xml",
    "schema-org.property-public.json",
    "schema-org.leaked-restricted-fields.invalid.json",
    "schema-org.status-draft.invalid.json",
    "schema-org.status-off-market.invalid.json",
    "schema-org.status-archived.invalid.json",
    "pending-change.owner-pii-protected.json",
    "processing-purpose.valid.json",
    "legal-basis-assessment.valid.json",
    "partner-relationship.active.json",
    "field-allowlist.active.json",
    "sharing-event.delivered.json",
    "data-subject-request.valid.json",
    "data-subject-request.deletion-fulfilled.json",
    "dsar-propagation.fulfilled.json",
    "retention-policy.valid.json",
    "automated-decision.reviewable.json",
    "legacy-import-qualification.approved.json",
)

# Channels that src/policy/evaluator.ts treats as public (masking branch).
PUBLIC_CHANNELS = frozenset({"website", "portal", "paid_ad"})

# Path segments that must never appear in a partner allowlist or ledger entry
# for a generic channel (classified as restricted by docs/privacy-operations.md).
RESTRICTED_PATH_SEGMENTS = frozenset({"tax_id", "cpf", "matricula", "owner"})

POLICY_ACTIONS = ("read", "write", "publish", "export", "send", "approve")


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------


def load_golden(name: str) -> dict[str, Any]:
    return json.loads((GOLDEN / name).read_text(encoding="utf-8"))


def schema_failures(name: str, schema_ref: str, payload: Any, expected: str) -> list[Any]:
    """Run the CI schema path (validate_conformance) against an arbitrary payload."""
    envelope = {"schema_ref": schema_ref, "payload": payload, "expected_result": expected}
    return conformance.validate_fixture_schema(SCHEMA, ROOT_VALIDATOR, GOLDEN / name, envelope)


def schema_accepts(name: str, schema_ref: str, payload: Any) -> bool:
    return schema_failures(name, schema_ref, payload, "valid") == []


def schema_rejects(name: str, schema_ref: str, payload: Any) -> bool:
    return schema_failures(name, schema_ref, payload, "invalid") == []


def is_valid_cpf(value: str) -> bool:
    """Check-digit validation, used only to prove fixture values are NOT real CPFs."""
    digits = re.sub(r"\D", "", value)
    if len(digits) != 11 or len(set(digits)) == 1:
        return False
    for length in (9, 10):
        total = sum(
            int(digit) * weight
            for digit, weight in zip(digits[:length], range(length + 1, 1, -1))
        )
        if (total * 10 % 11) % 10 != int(digits[length]):
            return False
    return True


CPF_SHAPE = re.compile(r"(?<![\w.\-])\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?![\w.\-])")


def iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_strings(item)


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


def property_public_columns() -> set[str]:
    """Output column names of the property_public view, parsed from db/schema.sql."""
    ddl = DDL_PATH.read_text(encoding="utf-8")
    body = ddl.split("CREATE VIEW property_public AS", 1)[1].split(
        "COMMENT ON VIEW property_public", 1
    )[0]
    select_list = body.split("SELECT", 1)[1].split("\nFROM property p", 1)[0]

    items: list[str] = []
    current: list[str] = []
    depth = 0
    for char in select_list:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        if char == "," and depth == 0:
            items.append("".join(current))
            current = []
        else:
            current.append(char)
    items.append("".join(current))

    names: set[str] = set()
    for item in items:
        flat = " ".join(item.split())
        alias = re.search(r"\bAS (\w+)$", flat)
        names.add(alias.group(1) if alias else flat.rsplit(".", 1)[-1])
    return names


# --------------------------------------------------------------------------
# C1/C2: default-deny policy, channels and approvals
# --------------------------------------------------------------------------


class TestDefaultDenyPolicy:
    NAME = "exposure-policy.default-deny.json"

    def envelope(self) -> dict[str, Any]:
        return load_golden(self.NAME)

    def policy(self) -> dict[str, Any]:
        return self.envelope()["payload"]

    def decide(self, role: str, action: str, field: str) -> tuple[str, str | None]:
        return conformance.evaluate_policy(self.policy(), role, action, field)

    def test_fixture_decisions_match_reference_evaluator(self) -> None:
        failures = conformance.validate_policy_decisions(GOLDEN / self.NAME, self.envelope())
        assert failures == [], [f.message for f in failures]

    def test_policy_default_is_deny_and_sensitive_reads_are_audited(self) -> None:
        policy = self.policy()
        assert policy["default_decision"] == "deny"
        assert policy["audit_sensitive_reads"] is True

    def test_unlisted_field_falls_to_default_deny(self) -> None:
        assert self.decide("public", "read", "headline") == ("deny", "default_decision")
        assert self.decide("public", "read", "address.street") == ("deny", "default_decision")

    def test_unlisted_action_falls_to_default_deny(self) -> None:
        for action in ("write", "publish", "send", "approve"):
            decision, reason = self.decide("director", action, "owner.tax_id")
            assert (decision, reason) == ("deny", "default_decision"), action

    @pytest.mark.parametrize("field", ["address.number", "owner.tax_id", "owner.tax_id.digits"])
    def test_sensitive_field_is_denied_for_every_role_without_explicit_allow(
        self, field: str
    ) -> None:
        roles = ("public", "portal", "broker", "crm", "anonymous", "unknown_role")
        for role in roles:
            for action in ("read", "export"):
                decision, _ = self.decide(role, action, field)
                assert decision == "deny", f"{role}:{action}:{field}"

    @staticmethod
    def allowed_pairs(policy: dict[str, Any], field: str) -> set[tuple[str, str]]:
        roles = ("public", "portal", "broker", "crm", "director", "anonymous")
        return {
            (role, action)
            for role in roles
            for action in POLICY_ACTIONS
            if conformance.evaluate_policy(policy, role, action, field)[0] == "allow"
        }

    def test_only_one_role_action_pair_can_read_owner_tax_id(self) -> None:
        assert self.allowed_pairs(self.policy(), "owner.tax_id") == {("director", "read")}

    def test_address_number_is_never_allowed(self) -> None:
        roles = ("public", "portal", "broker", "crm", "director", "anonymous")
        for role in roles:
            for action in POLICY_ACTIONS:
                assert self.decide(role, action, "address.number")[0] == "deny", (role, action)

    def test_broker_street_access_requires_the_broker_role(self) -> None:
        assert self.decide("broker", "read", "address.street")[0] == "allow"
        assert self.decide("portal", "read", "address.street")[0] == "deny"

    def test_public_channels_are_not_in_allowed_channels(self) -> None:
        allowed = set(self.policy()["allowed_channels"])
        assert allowed, "a confidential policy must declare its channels explicitly"
        assert "*" not in allowed
        assert not (allowed & PUBLIC_CHANNELS), allowed & PUBLIC_CHANNELS

    def test_export_and_send_require_approval(self) -> None:
        assert {"export", "send"} <= set(self.policy()["requires_approval_for"])

    # Mutation-style: the gate must fail when the protection is removed.

    def test_gate_detects_default_decision_flipped_to_allow(self) -> None:
        envelope = self.envelope()
        envelope["payload"]["default_decision"] = "allow"
        assert conformance.validate_policy_decisions(GOLDEN / self.NAME, envelope)

    def test_gate_detects_removed_sensitive_field_deny_rule(self) -> None:
        envelope = self.envelope()
        envelope["payload"]["rules"] = [
            rule
            for rule in envelope["payload"]["rules"]
            if rule["reason_code"] != "sensitive_field_default_deny"
        ]
        assert conformance.validate_policy_decisions(GOLDEN / self.NAME, envelope)

    def test_role_pair_property_detects_privilege_widened_to_every_role(self) -> None:
        # The fixture's expected_decisions do not cover this mutation (only the
        # director is asked about owner.tax_id), so the pair-set property above
        # is the control that catches it. Prove that it does.
        policy = self.policy()
        for rule in policy["rules"]:
            if rule["reason_code"] == "director_pii_access":
                rule["roles"] = []
        assert self.allowed_pairs(policy, "owner.tax_id") != {("director", "read")}


# --------------------------------------------------------------------------
# C3: masked listing projection (website / portal / paid_ad)
# --------------------------------------------------------------------------


class TestListingProjection:
    NAME = "listing.public-masked.json"

    def envelope(self) -> dict[str, Any]:
        return load_golden(self.NAME)

    def failures(self, envelope: dict[str, Any]) -> list[Any]:
        return conformance.validate_projection(GOLDEN / self.NAME, envelope)

    def test_fixture_projection_honors_masking(self) -> None:
        assert self.failures(self.envelope()) == []

    def test_fixture_is_masked_by_declaration(self) -> None:
        payload = self.envelope()["payload"]
        assert payload["price_display"] != "visible"
        assert payload["address_display"] in {"approximate", "hidden"}

    def test_projection_exposes_no_street_or_number(self) -> None:
        expectation = self.envelope()["projection_expectation"]
        assert expectation["address.street"] is None
        assert expectation["address.number"] is None

    @pytest.mark.parametrize(
        ("label", "mutate"),
        [
            ("numeric price under on_request", lambda e: e["projection_expectation"].update(price="17500000.00")),
            ("street under approximate", lambda e: e["projection_expectation"].update({"address.street": "Rua Exemplo"})),
            ("number under approximate", lambda e: e["projection_expectation"].update({"address.number": "100"})),
            (
                "neighborhood under hidden",
                lambda e: e["payload"].update(address_display="hidden"),
            ),
        ],
    )
    def test_gate_detects_leaking_projection(self, label: str, mutate: Any) -> None:
        envelope = self.envelope()
        mutate(envelope)
        assert self.failures(envelope), label

    def test_numeric_price_is_allowed_only_when_price_display_is_visible(self) -> None:
        envelope = self.envelope()
        envelope["payload"]["price_display"] = "visible"
        envelope["projection_expectation"]["price"] = "17500000.00"
        assert self.failures(envelope) == []


# --------------------------------------------------------------------------
# C4: portal XML feed
# --------------------------------------------------------------------------


class TestPortalFeed:
    PATH = GOLDEN / "portal-feed.valid.xml"
    RESTRICTED_TAGS = frozenset(
        {
            "matricula", "taxid", "tax_id", "cpf", "owner", "ownername",
            "street", "streetnumber", "addressnumber", "latitude", "longitude",
            "liquidityscore", "matchscore",
        }
    )

    def feed_failures(self, text: str, tmp_path: Path) -> list[Any]:
        path = tmp_path / "feed.xml"
        path.write_text(text, encoding="utf-8")
        return conformance.validate_portal_feed(path)

    def test_golden_feed_passes(self) -> None:
        assert conformance.validate_portal_feed(self.PATH) == []

    def test_feed_declares_masked_address_and_no_restricted_elements(self) -> None:
        root = ET.parse(self.PATH).getroot()
        tags = {element.tag.lower() for element in root.iter()}
        assert not (tags & self.RESTRICTED_TAGS), tags & self.RESTRICTED_TAGS
        for listing in root.findall("Listing"):
            assert listing.findtext("AddressDisplay") in {"approximate", "hidden"}
            assert listing.find("Price") is None

    def test_feed_carries_no_cpf_shaped_value(self) -> None:
        text = self.PATH.read_text(encoding="utf-8")
        assert [m for m in CPF_SHAPE.findall(text) if is_valid_cpf(m)] == []

    def test_gate_detects_numeric_price_without_visible_display(self, tmp_path: Path) -> None:
        text = self.PATH.read_text(encoding="utf-8").replace(
            "</Listing>", "    <Price>17500000.00</Price>\n  </Listing>"
        )
        failures = self.feed_failures(text, tmp_path)
        assert failures
        assert "PriceDisplay=visible" in failures[0].message

    def test_price_is_allowed_when_display_is_visible(self, tmp_path: Path) -> None:
        text = (
            self.PATH.read_text(encoding="utf-8")
            .replace("</Listing>", "    <Price>17500000.00</Price>\n  </Listing>")
            .replace("<PriceDisplay>on_request</PriceDisplay>", "<PriceDisplay>visible</PriceDisplay>")
        )
        assert self.feed_failures(text, tmp_path) == []

    def test_gate_detects_malformed_feed(self, tmp_path: Path) -> None:
        failures = self.feed_failures("<Listings><Listing></Listings>", tmp_path)
        assert failures
        assert "malformed XML" in failures[0].message


# --------------------------------------------------------------------------
# C5: property_public view (static text; behavior is tests/postgres)
# --------------------------------------------------------------------------


class TestPublicSurfaceDdl:
    RESTRICTED_COLUMNS = frozenset(
        {
            "matricula", "owner", "owner_id", "tax_id", "latitude", "longitude",
            "addr_street", "addr_number", "liquidity_score", "match_score",
            "rarity_score", "off_market_potential", "documents",
        }
    )

    def test_ci_ddl_gate_passes(self) -> None:
        failures = conformance.validate_public_projection_ddl()
        assert failures == [], [f.message for f in failures]

    def test_view_exposes_no_restricted_column(self) -> None:
        columns = property_public_columns()
        assert columns, "the column parser found nothing; the view layout changed"
        assert not (columns & self.RESTRICTED_COLUMNS), columns & self.RESTRICTED_COLUMNS

    def test_exporter_surface_equals_view_columns(self) -> None:
        # The exporter's allowlist and the DDL must describe the same surface,
        # otherwise one of them silently widens or narrows the public boundary.
        assert property_public_columns() == set(schema_org.PUBLIC_SURFACE)

    @pytest.mark.parametrize(
        ("original", "replacement", "expected"),
        [
            ("l.address_display = 'hidden'", "l.address_display = 'never'", "hidden address suppression"),
            ("candidate.exposure_level = 'public'", "candidate.exposure_level IS NOT NULL", "explicit public exposure"),
            (
                "p.property_status NOT IN ('draft', 'off_market', 'archived')",
                "p.property_status IS NOT NULL",
                "unpublishable status filter",
            ),
            (
                "COMMENT ON VIEW property_public",
                "-- THEN pf.latitude\nCOMMENT ON VIEW property_public",
                "exact latitude passthrough",
            ),
        ],
    )
    def test_gate_detects_weakened_view(
        self,
        original: str,
        replacement: str,
        expected: str,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ddl = DDL_PATH.read_text(encoding="utf-8")
        assert original in ddl, "mutation target moved; update this test"
        mutated = tmp_path / "schema.sql"
        mutated.write_text(ddl.replace(original, replacement), encoding="utf-8")
        monkeypatch.setattr(conformance, "DDL_PATH", mutated)
        failures = conformance.validate_public_projection_ddl()
        assert any(expected in failure.message for failure in failures), [
            f.message for f in failures
        ]


# --------------------------------------------------------------------------
# C6/C7: schema.org export channel
# --------------------------------------------------------------------------


class TestSchemaOrgChannel:
    def record(self) -> dict[str, Any]:
        return copy.deepcopy(load_golden("schema-org.property-public.json")["record"])

    def test_ci_schema_org_cases_pass(self) -> None:
        failures = conformance.validate_schema_org_cases()
        assert failures == [], [f.message for f in failures]

    def test_public_record_exports_exact_price_without_float(self) -> None:
        document = schema_org.export(self.record())
        assert document["offers"][0]["price"] == "17500000.00"
        assert isinstance(document["offers"][0]["price"], str)

    def test_export_has_no_restricted_keys_and_only_approximate_coordinates(self) -> None:
        document = schema_org.export(self.record())
        text = json.dumps(document, ensure_ascii=False)
        # latitude/longitude are legitimate schema.org GeoCoordinates keys, so
        # they are checked by precision below instead of by name.
        leaked = [
            name
            for name in sorted(schema_org.FORBIDDEN_FIELDS - {"latitude", "longitude"})
            if f'"{name}"' in text
        ]
        assert leaked == []
        geo = document["mainEntity"]["geo"]
        for axis in ("latitude", "longitude"):
            assert round(geo[axis], 2) == geo[axis], f"{axis} is more precise than the view allows"

    def test_surface_and_forbidden_sets_do_not_overlap(self) -> None:
        assert not (schema_org.PUBLIC_SURFACE & schema_org.FORBIDDEN_FIELDS)

    @pytest.mark.parametrize("field", sorted(schema_org.FORBIDDEN_FIELDS))
    def test_exporter_rejects_each_restricted_field(self, field: str) -> None:
        record = self.record()
        record[field] = "synthetic"
        with pytest.raises(schema_org.ExportError, match="restricted fields"):
            schema_org.export(record)

    def test_exporter_rejects_field_outside_public_surface(self) -> None:
        record = self.record()
        record["internal_note"] = "synthetic"
        with pytest.raises(schema_org.ExportError, match="outside property_public"):
            schema_org.export(record)

    @pytest.mark.parametrize("status", sorted(schema_org.UNPUBLISHABLE_STATUS))
    def test_exporter_rejects_unpublishable_status(self, status: str) -> None:
        record = self.record()
        record["property_status"] = status
        with pytest.raises(schema_org.ExportError, match="not publishable"):
            schema_org.export(record)

    def test_negative_fixtures_are_the_ones_the_gate_exercises(self) -> None:
        negatives = {
            case["fixture_path"]
            for case in json.loads(CASES_PATH.read_text(encoding="utf-8"))
            if case.get("validator") == "schema-org" and case["expected_result"] == "invalid"
        }
        assert negatives == {
            "tests/golden/schema-org.leaked-restricted-fields.invalid.json",
            "tests/golden/schema-org.status-draft.invalid.json",
            "tests/golden/schema-org.status-off-market.invalid.json",
            "tests/golden/schema-org.status-archived.invalid.json",
        }


# --------------------------------------------------------------------------
# C8/C9: owner PII and synthetic data
# --------------------------------------------------------------------------


class TestOwnerPiiAndSyntheticData:
    def test_external_source_cannot_overwrite_owner_pii_without_review(self) -> None:
        change = load_golden("pending-change.owner-pii-protected.json")
        assert change["field_class"] == "pii"
        assert change["expected_state"] == "pending_review"
        assert change["expected_reason"] == "external_source_cannot_write_pii_without_review"
        # Fixture convention: a higher tier number is a lower trust source.
        assert change["trust_tier"] > change["current_snapshot"]["trust_tier"]

    def test_current_snapshot_does_not_carry_a_real_looking_identifier(self) -> None:
        snapshot = load_golden("pending-change.owner-pii-protected.json")["current_snapshot"]
        assert snapshot["tax_id"].startswith("<redacted")

    def test_cpf_checker_accepts_a_known_valid_and_rejects_synthetic_values(self) -> None:
        assert is_valid_cpf("52998224725")
        assert is_valid_cpf("529.982.247-25")
        assert not is_valid_cpf("52998224724")
        assert not is_valid_cpf("00000000000")
        assert not is_valid_cpf("11111111111")

    def test_no_golden_fixture_contains_a_valid_cpf(self) -> None:
        offenders: list[str] = []
        for path in sorted(GOLDEN.iterdir()):
            text = path.read_text(encoding="utf-8")
            offenders.extend(
                f"{path.name}: {match}"
                for match in CPF_SHAPE.findall(text)
                if is_valid_cpf(match)
            )
        assert offenders == [], "fixtures must use synthetic data only"


# --------------------------------------------------------------------------
# C10-C13: purpose, basis, partner, allowlist, ledger
# --------------------------------------------------------------------------


SCHEMA_CHECKED_FIXTURES = (
    ("exposure-policy.default-deny.json", "#/$defs/ExposurePolicy"),
    ("listing.public-masked.json", "#/$defs/Listing"),
    ("processing-purpose.valid.json", "#/$defs/ProcessingPurpose"),
    ("legal-basis-assessment.valid.json", "#/$defs/LegalBasisAssessment"),
    ("partner-relationship.active.json", "#/$defs/PartnerRelationship"),
    ("field-allowlist.active.json", "#/$defs/FieldAllowlist"),
    ("sharing-event.delivered.json", "#/$defs/SharingEvent"),
    ("data-subject-request.valid.json", "#/$defs/DataSubjectRequest"),
    ("data-subject-request.deletion-fulfilled.json", "#/$defs/DataSubjectRequest"),
    ("dsar-propagation.fulfilled.json", "#/$defs/DSARPropagation"),
    ("retention-policy.valid.json", "#/$defs/RetentionPolicy"),
    ("automated-decision.reviewable.json", "#/$defs/AutomatedDecisionRecord"),
    ("legacy-import-qualification.approved.json", "#/$defs/LegacyImportQualification"),
)


@pytest.mark.parametrize(("name", "ref"), SCHEMA_CHECKED_FIXTURES)
def test_privacy_fixture_validates_against_its_schema(name: str, ref: str) -> None:
    envelope = load_golden(name)
    assert envelope["schema_ref"] == ref
    assert schema_accepts(name, ref, envelope["payload"])


class TestPartnerAllowlistAndLedger:
    def allowlist(self) -> dict[str, Any]:
        return load_golden("field-allowlist.active.json")["payload"]

    def event(self) -> dict[str, Any]:
        return load_golden("sharing-event.delivered.json")["payload"]

    def partner(self) -> dict[str, Any]:
        return load_golden("partner-relationship.active.json")["payload"]

    def test_partner_has_contract_dpa_and_dsar_contact_before_any_flow(self) -> None:
        partner = self.partner()
        assert partner["active"] is True
        assert partner["contract_ref"]
        assert partner["dpa_ref"]
        assert partner["dsar_contact_ref"], "propagation needs a partner contact"
        assert partner["valid_until"] is None or partner["valid_until"] >= partner["valid_from"]

    def test_allowlist_is_active_versioned_approved_and_minimal(self) -> None:
        allowlist = self.allowlist()
        assert allowlist["status"] == "active"
        assert allowlist["version"] >= 1
        assert allowlist["approved_by"] and allowlist["approved_at"]
        assert allowlist["allowed_fields"], "default-deny: an empty allowlist shares nothing"

    def test_allowlist_contains_no_restricted_field_path(self) -> None:
        for path in self.allowlist()["allowed_fields"]:
            assert not (set(path.split(".")) & RESTRICTED_PATH_SEGMENTS), path

    def test_ledger_shares_only_allowlisted_fields_at_the_allowlist_version(self) -> None:
        allowlist, event = self.allowlist(), self.event()
        assert set(event["shared_fields"]) <= set(allowlist["allowed_fields"])
        assert event["field_allowlist_version"] == allowlist["version"]

    def test_ledger_records_field_paths_and_digest_not_values(self) -> None:
        event = self.event()
        path_shape = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)*$")
        assert all(path_shape.match(path) for path in event["shared_fields"])
        assert event["payload_digest"].startswith("sha256:")
        assert not [s for s in iter_strings(event) if "@" in s], "ledger must not copy PII"
        assert event["record_count"] >= 0

    @pytest.mark.parametrize("extra", [{"payload": {"email": "x"}}, {"email": "x"}, {"tax_id": "x"}])
    def test_ledger_schema_rejects_copied_payload(self, extra: dict[str, Any]) -> None:
        payload = {**self.event(), **extra}
        assert schema_rejects("sharing-event.delivered.json", "#/$defs/SharingEvent", payload)

    def test_ledger_schema_rejects_empty_shared_fields(self) -> None:
        payload = {**self.event(), "shared_fields": []}
        assert schema_rejects("sharing-event.delivered.json", "#/$defs/SharingEvent", payload)

    def test_allowlist_schema_rejects_empty_field_selection(self) -> None:
        payload = {**self.allowlist(), "allowed_fields": []}
        assert schema_rejects("field-allowlist.active.json", "#/$defs/FieldAllowlist", payload)

    def test_partner_schema_rejects_missing_dpa_reference(self) -> None:
        payload = {k: v for k, v in self.partner().items() if k != "dpa_ref"}
        assert schema_rejects("partner-relationship.active.json", "#/$defs/PartnerRelationship", payload)

    def test_legal_basis_and_purpose_are_explicit_and_owned(self) -> None:
        purpose = load_golden("processing-purpose.valid.json")["payload"]
        basis = load_golden("legal-basis-assessment.valid.json")["payload"]
        assert purpose["active"] is True
        assert purpose["owner_role"] and purpose["data_categories"]
        assert basis["status"] == "approved"
        assert basis["safeguards"] and basis["evidence_ref"]


# --------------------------------------------------------------------------
# C14-C17: DSAR, retention, automated decision, legacy import
# --------------------------------------------------------------------------


class TestDsarRetentionAndDecisions:
    def test_propagation_fulfilled_carries_ordered_evidence(self) -> None:
        propagation = load_golden("dsar-propagation.fulfilled.json")["payload"]
        assert propagation["status"] == "fulfilled"
        assert propagation["evidence_ref"]
        assert propagation["failure_code"] is None
        stamps = [
            parse_ts(propagation[key])
            for key in ("sent_at", "acknowledged_at", "fulfilled_at", "due_at")
        ]
        assert stamps == sorted(stamps)

    def test_deletion_request_records_concrete_effect_within_deadline(self) -> None:
        request = load_golden("data-subject-request.deletion-fulfilled.json")["payload"]
        assert request["request_type"] == "deletion"
        assert request["status"] == "fulfilled"
        assert request["resolution_action"] in {"delete", "anonymize"}
        assert request["affected_record_ids"]
        assert request["audit_log_ref"]
        assert (
            parse_ts(request["requested_at"])
            <= parse_ts(request["fulfilled_at"])
            <= parse_ts(request["due_at"])
        )

    def test_retention_policy_is_bound_to_basis_purpose_and_an_action(self) -> None:
        policy = load_golden("retention-policy.valid.json")["payload"]
        assert policy["legal_basis"] and policy["processing_purpose"]
        assert policy["retention_period_days"] > 0
        assert policy["action_on_expiry"] in {"delete", "anonymize", "review", "archive"}
        assert "party.tax_id" in policy["applies_to"]

    def test_sole_automated_decision_exposes_review_and_explanation(self) -> None:
        decision = load_golden("automated-decision.reviewable.json")["payload"]
        assert decision["sole_automated"] is True
        assert decision["review_status"] != "not_requested"
        assert decision["review_request_ref"] and decision["explanation_ref"]

    def test_legacy_wave_is_qualified_before_import(self) -> None:
        wave = load_golden("legacy-import-qualification.approved.json")["payload"]
        assert wave["status"] == "approved"
        assert wave["origin_verified"] and wave["purpose_compatible"] and wave["suppression_applied"]
        assert wave["evidence_ref"]

    def test_gap_fulfilled_propagation_without_evidence_is_rejected(self) -> None:
        payload = load_golden("dsar-propagation.fulfilled.json")["payload"]
        payload["evidence_ref"] = None
        assert schema_rejects("dsar-propagation.fulfilled.json", "#/$defs/DSARPropagation", payload)

    def test_gap_fulfilled_deletion_without_effect_is_rejected(self) -> None:
        payload = load_golden("data-subject-request.deletion-fulfilled.json")["payload"]
        del payload["resolution_action"]
        payload["affected_record_ids"] = []
        assert schema_rejects(
            "data-subject-request.deletion-fulfilled.json", "#/$defs/DataSubjectRequest", payload
        )


# --------------------------------------------------------------------------
# traceability: docs/privacy-verification.md <-> fixtures <-> this suite
# --------------------------------------------------------------------------


class TestVerificationDocTraceability:
    def doc(self) -> str:
        assert DOC_PATH.exists(), "docs/privacy-verification.md is missing"
        return DOC_PATH.read_text(encoding="utf-8")

    def test_every_privacy_fixture_exists_and_is_in_the_conformance_index(self) -> None:
        indexed = {
            case["fixture_path"]
            for case in json.loads(CASES_PATH.read_text(encoding="utf-8"))
        }
        for name in PRIVACY_FIXTURES:
            assert (GOLDEN / name).exists(), name
            assert f"tests/golden/{name}" in indexed, name

    def test_doc_mentions_every_privacy_fixture(self) -> None:
        doc = self.doc()
        missing = [name for name in PRIVACY_FIXTURES if f"tests/golden/{name}" not in doc]
        assert missing == []

    def test_every_fixture_path_in_the_doc_exists(self) -> None:
        mentioned = set(re.findall(r"tests/golden/[\w.\-]+", self.doc()))
        missing = sorted(path for path in mentioned if not (ROOT / path).exists())
        assert missing == []

    def test_doc_points_at_this_suite_and_separates_tested_from_operator_duties(self) -> None:
        doc = self.doc()
        assert "tests/contracts/test_privacy_channels.py" in doc
        for title in ("Controle testado e obrigação do operador", "Lacunas conhecidas"):
            assert re.search(rf"^## (\d+\. )?{title}$", doc, re.MULTILINE), title

    def test_doc_lists_every_pinned_gap(self) -> None:
        doc = self.doc()
        for gap in ("GAP-01", "GAP-02"):
            assert gap in doc, gap
