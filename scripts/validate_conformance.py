#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.13.9"
# dependencies = [
#     "jsonschema[format]==4.26.0",
# ]
# ///

# ─── How to run ───
# 1. Install uv 0.9.7 (if not installed):
#      curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Run directly (no venv, no pip install needed):
#      uv run scripts/validate_conformance.py
# 3. Or make executable and run:
#      chmod +x scripts/validate_conformance.py && ./scripts/validate_conformance.py
# ──────────────────

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

from jsonschema import Draft202012Validator

type JsonPrimitive = bool | float | int | str | None
type JsonValue = JsonPrimitive | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schema" / "mbras.schema.json"
GOLDEN_DIR = ROOT / "tests" / "golden"
CONFORMANCE_CASES_PATH = GOLDEN_DIR / "conformance-cases.json"


@dataclass(frozen=True, slots=True)
class CheckFailure:
    path: Path
    message: str


@dataclass(frozen=True, slots=True)
class FixtureShapeError(Exception):
    location: str
    expected: str

    def __str__(self) -> str:
        return f"{self.location}: expected {self.expected}"


def load_json(path: Path) -> JsonValue:
    return json.loads(path.read_text(encoding="utf-8"))


def as_object(value: JsonValue, location: str) -> JsonObject:
    if isinstance(value, dict):
        return value
    raise FixtureShapeError(location=location, expected="JSON object")


def as_array(value: JsonValue, location: str) -> list[JsonValue]:
    if isinstance(value, list):
        return value
    raise FixtureShapeError(location=location, expected="JSON array")


def as_string(value: JsonValue, location: str) -> str:
    if isinstance(value, str):
        return value
    raise FixtureShapeError(location=location, expected="string")


def optional_string(value: JsonValue, location: str) -> str | None:
    if value is None:
        return None
    return as_string(value, location)


def string_list(value: JsonValue | None, location: str) -> list[str]:
    if value is None:
        return []
    return [as_string(item, f"{location}[]") for item in as_array(value, location)]


def relative(path: Path) -> Path:
    return path.relative_to(ROOT)


def schema_target(schema: JsonObject, schema_ref: str) -> JsonObject:
    prefix = "#/$defs/"
    if not schema_ref.startswith(prefix):
        raise FixtureShapeError(location="schema_ref", expected=f"{prefix}<Definition>")
    defs = as_object(schema["$defs"], "schema.$defs")
    return as_object(defs[schema_ref.removeprefix(prefix)], f"schema.{schema_ref}")


def validate_fixture_schema(
    schema: JsonObject,
    root_validator: Draft202012Validator,
    fixture_path: Path,
    envelope: JsonObject,
) -> list[CheckFailure]:
    schema_ref = envelope.get("schema_ref")
    if schema_ref is None:
        # An "invalid" case can only be demonstrated through schema validation,
        # so it must declare schema_ref; otherwise the negative test is vacuous.
        if envelope.get("expected_result") == "invalid":
            return [CheckFailure(fixture_path, "invalid case must declare schema_ref to be verifiable")]
        return []

    target = schema_target(schema, as_string(schema_ref, f"{relative(fixture_path)}.schema_ref"))
    payload = envelope.get("payload")
    if payload is None:
        raise FixtureShapeError(location=f"{relative(fixture_path)}.payload", expected="payload")

    expected_result = as_string(
        envelope.get("expected_result"),
        f"{relative(fixture_path)}.expected_result",
    )
    validator = root_validator.evolve(schema=target)
    errors = sorted(validator.iter_errors(payload), key=lambda error: error.json_path)

    if expected_result == "valid":
        if errors:
            first = errors[0]
            return [CheckFailure(fixture_path, f"expected valid, got {first.json_path}: {first.message}")]
        return []
    if expected_result == "invalid":
        if errors:
            return []
        return [CheckFailure(fixture_path, "expected invalid, but schema accepted payload")]
    return [CheckFailure(fixture_path, f"unsupported expected_result {expected_result!r}")]


def field_matches(rule_field: str, requested_field: str) -> bool:
    return rule_field == requested_field or requested_field.startswith(f"{rule_field}.")


def conditions_match(conditions: JsonObject, subject_role: str) -> bool:
    for key, value in conditions.items():
        if key == "broker_is_assigned" and value is True:
            if subject_role != "broker":
                return False
            continue
        return False
    return True


def rule_matches(rule: JsonObject, subject_role: str, action: str, field: str) -> bool:
    actions = string_list(rule.get("actions"), "rule.actions")
    if action not in actions:
        return False

    fields = string_list(rule.get("fields"), "rule.fields")
    if fields and not any(field_matches(rule_field, field) for rule_field in fields):
        return False

    roles = string_list(rule.get("roles"), "rule.roles")
    if roles and subject_role not in roles:
        return False

    conditions = as_object(rule.get("conditions") or {}, "rule.conditions")
    return conditions_match(conditions, subject_role)


def rule_priority(rule: JsonObject) -> int:
    value = rule.get("priority")
    if isinstance(value, bool):
        return 0
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def evaluate_policy(policy: JsonObject, subject_role: str, action: str, field: str) -> tuple[str, str | None]:
    rules = [as_object(rule, "policy.rules[]") for rule in as_array(policy.get("rules") or [], "policy.rules")]
    matches = [rule for rule in rules if rule_matches(rule, subject_role, action, field)]
    if not matches:
        return as_string(policy.get("default_decision"), "policy.default_decision"), "default_decision"

    # Highest priority wins; within the top priority band, deny beats allow.
    top = max(rule_priority(rule) for rule in matches)
    top_rules = [rule for rule in matches if rule_priority(rule) == top]

    for rule in top_rules:
        if as_string(rule.get("effect"), "rule.effect") == "deny":
            return "deny", optional_string(rule.get("reason_code"), "rule.reason_code")
    for rule in top_rules:
        if as_string(rule.get("effect"), "rule.effect") == "allow":
            return "allow", optional_string(rule.get("reason_code"), "rule.reason_code")

    return as_string(policy.get("default_decision"), "policy.default_decision"), "default_decision"


def validate_policy_decisions(fixture_path: Path, envelope: JsonObject) -> list[CheckFailure]:
    expectations = envelope.get("expected_decisions")
    if expectations is None:
        return []

    policy = as_object(envelope.get("payload"), f"{relative(fixture_path)}.payload")
    failures: list[CheckFailure] = []
    for value in as_array(expectations, f"{relative(fixture_path)}.expected_decisions"):
        expected = as_object(value, "expected_decisions[]")
        subject_role = as_string(expected.get("subject_role"), "expected.subject_role")
        action = as_string(expected.get("action"), "expected.action")
        field = as_string(expected.get("field"), "expected.field")
        expected_decision = as_string(expected.get("decision"), "expected.decision")
        expected_reason = optional_string(expected.get("reason_code"), "expected.reason_code")
        decision, reason = evaluate_policy(policy, subject_role, action, field)

        if decision != expected_decision or reason != expected_reason:
            failures.append(
                CheckFailure(
                    fixture_path,
                    f"{subject_role}:{action}:{field} expected {expected_decision}/{expected_reason}, got {decision}/{reason}",
                ),
            )
    return failures


def looks_numeric(value: JsonValue) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        stripped = value.strip().replace(".", "").replace(",", "").replace(" ", "")
        return stripped.isdigit() and stripped != ""
    return False


def validate_projection(fixture_path: Path, envelope: JsonObject) -> list[CheckFailure]:
    """Enforce that a declared projection_expectation honors the listing's masking settings.

    This makes the masking contract executable instead of decorative: a projection that
    leaks a numeric price under on_request, or a street/number under a masked address,
    now fails the conformance run.
    """
    raw = envelope.get("projection_expectation")
    if raw is None:
        return []
    expectation = as_object(raw, f"{relative(fixture_path)}.projection_expectation")
    payload = as_object(envelope.get("payload"), f"{relative(fixture_path)}.payload")
    failures: list[CheckFailure] = []

    price_display = payload.get("price_display")
    if price_display is not None and price_display != "visible" and "price" in expectation:
        price = expectation.get("price")
        if looks_numeric(price):
            failures.append(CheckFailure(fixture_path, f"price_display={price_display} but projection exposes numeric price {price!r}"))

    address_display = payload.get("address_display")
    if address_display in ("approximate", "hidden"):
        for masked_field in ("address.street", "address.number"):
            if masked_field in expectation and expectation.get(masked_field) is not None:
                failures.append(CheckFailure(fixture_path, f"address_display={address_display} but projection exposes {masked_field}={expectation.get(masked_field)!r}"))
    if address_display == "hidden" and expectation.get("neighborhood") is not None:
        failures.append(CheckFailure(fixture_path, "address_display=hidden but projection exposes neighborhood"))

    return failures


def validate_portal_feed(path: Path) -> list[CheckFailure]:
    try:
        document = ET.parse(path)
    except ET.ParseError as exc:
        return [CheckFailure(path, f"malformed XML: {exc}")]
    failures: list[CheckFailure] = []
    for listing in document.findall("Listing"):
        price = listing.find("Price")
        price_display = listing.findtext("PriceDisplay")
        if price is not None and price_display != "visible":
            external_id = listing.findtext("ExternalId") or "<unknown>"
            failures.append(
                CheckFailure(
                    path,
                    f"listing {external_id} exposes numeric Price without PriceDisplay=visible",
                ),
            )
    return failures


def validate_case_index() -> list[CheckFailure]:
    raw_cases = as_array(load_json(CONFORMANCE_CASES_PATH), "conformance-cases")
    referenced: set[Path] = set()
    failures: list[CheckFailure] = []

    for raw_case in raw_cases:
        case = as_object(raw_case, "conformance-cases[]")
        case_id = as_string(case.get("id"), "case.id")
        fixture_path = ROOT / as_string(case.get("fixture_path"), f"{case_id}.fixture_path")
        referenced.add(fixture_path)

        if not fixture_path.exists():
            failures.append(CheckFailure(CONFORMANCE_CASES_PATH, f"{case_id} points to missing fixture {relative(fixture_path)}"))
            continue

        if fixture_path.suffix == ".json":
            fixture = as_object(load_json(fixture_path), str(relative(fixture_path)))
            fixture_id = optional_string(fixture.get("id"), f"{relative(fixture_path)}.id")
            if fixture_id is not None and fixture_id != case_id:
                failures.append(CheckFailure(fixture_path, f"fixture id {fixture_id!r} differs from case id {case_id!r}"))

            applies_to = string_list(case.get("applies_to"), f"{case_id}.applies_to")
            if "schema" in applies_to and fixture.get("schema_ref") is None:
                failures.append(CheckFailure(fixture_path, "schema case must declare schema_ref"))

            fixture_expected = optional_string(fixture.get("expected_result"), f"{relative(fixture_path)}.expected_result")
            case_expected = as_string(case.get("expected_result"), f"{case_id}.expected_result")
            if fixture_expected is not None and fixture_expected != case_expected:
                failures.append(
                    CheckFailure(fixture_path, f"fixture expected_result {fixture_expected!r} differs from case {case_expected!r}"),
                )

    all_fixtures = {path for path in GOLDEN_DIR.iterdir() if path.name != "conformance-cases.json"}
    for orphan in sorted(all_fixtures - referenced):
        failures.append(CheckFailure(orphan, "fixture is not referenced by conformance-cases.json"))

    return failures


def run() -> list[CheckFailure]:
    schema = as_object(load_json(SCHEMA_PATH), str(relative(SCHEMA_PATH)))
    Draft202012Validator.check_schema(schema)
    # FORMAT_CHECKER makes format assertions (uuid, date-time, email, uri) actually
    # fail validation instead of being silently treated as annotations.
    root_validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    failures = validate_case_index()
    for fixture_path in sorted(GOLDEN_DIR.iterdir()):
        if fixture_path.name == "conformance-cases.json":
            continue
        if fixture_path.suffix == ".json":
            envelope = as_object(load_json(fixture_path), str(relative(fixture_path)))
            failures.extend(validate_fixture_schema(schema, root_validator, fixture_path, envelope))
            failures.extend(validate_policy_decisions(fixture_path, envelope))
            failures.extend(validate_projection(fixture_path, envelope))
            continue
        if fixture_path.suffix == ".xml":
            failures.extend(validate_portal_feed(fixture_path))
    return failures


def main() -> int:
    failures = run()
    if not failures:
        print("PASS: conformance fixtures validated")
        return 0

    for failure in failures:
        print(f"FAIL {relative(failure.path)}: {failure.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
