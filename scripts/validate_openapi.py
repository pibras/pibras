#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.13.9"
# dependencies = [
#     "PyYAML==6.0.3",
# ]
# ///

# ─── How to run ───
# 1. Install uv 0.9.7 (if not installed):
#      curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Run directly (no venv, no pip install needed):
#      uv run scripts/validate_openapi.py
# 3. Or make executable and run:
#      chmod +x scripts/validate_openapi.py && ./scripts/validate_openapi.py
# ──────────────────

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

type Scalar = bool | float | int | str | None
type YamlValue = Scalar | list[YamlValue] | dict[str, YamlValue]
type YamlObject = dict[str, YamlValue]

ROOT: Final = Path(__file__).resolve().parents[1]
OPENAPI_PATH: Final = ROOT / "openapi.yaml"
SCHEMA_PATH: Final = ROOT / "schema" / "mbras.schema.json"
APPROVED_SCHEMA_REF_ROOT: Final = "./schema/mbras.schema.json#/$defs/"
COMPONENT_REF_ROOT: Final = "#/components/"
REQUIRED_PATHS: Final = frozenset(
    (
        "/units/{unit_id}",
        "/properties/{property_id}",
        "/listings/{listing_id}",
        "/properties/{property_id}/exposure-policy",
        "/conformance/cases",
        "/privacy/sharing-decisions",
        "/privacy/sharing-events",
        "/privacy/dsar-propagations",
    )
)
# Every operation must declare the secured error surface; parameterized
# operations must additionally declare 400 (path-parameter validation)
# and 404 (missing resource).
SECURITY_RESPONSES: Final = frozenset(("401", "403"))
PARAMETERIZED_RESPONSES: Final = frozenset(("400", "404"))
PATH_TEMPLATE: Final = re.compile(r"\{([^{}]+)\}")


@dataclass(frozen=True, slots=True)
class CheckFailure:
    path: Path
    message: str


@dataclass(frozen=True, slots=True)
class ShapeError(Exception):
    location: str
    expected: str

    def __str__(self) -> str:
        return f"{self.location}: expected {self.expected}"


def normalize(value, location: str) -> YamlValue:
    if value is None:
        return None
    if isinstance(value, bool | int | float | str):
        return value
    if isinstance(value, list):
        return [normalize(item, f"{location}[]") for item in value]
    if isinstance(value, dict):
        normalized: YamlObject = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise ShapeError(location=location, expected="string keys")
            normalized[key] = normalize(item, f"{location}.{key}")
        return normalized
    raise ShapeError(location=location, expected="YAML scalar, array, or object")


def load_yaml(path: Path) -> YamlValue:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ShapeError(location=str(path), expected=f"valid YAML ({exc})") from exc
    return normalize(loaded, str(path))


def load_json(path: Path) -> YamlValue:
    return normalize(json.loads(path.read_text(encoding="utf-8")), str(path))


def as_object(value: YamlValue | None, location: str) -> YamlObject:
    if isinstance(value, dict):
        return value
    raise ShapeError(location=location, expected="object")


def as_string(value: YamlValue | None, location: str) -> str:
    if isinstance(value, str):
        return value
    raise ShapeError(location=location, expected="string")


def references(value: YamlValue) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        ref = value.get("$ref")
        if isinstance(ref, str):
            refs.append(ref)
        for child in value.values():
            refs.extend(references(child))
    if isinstance(value, list):
        for child in value:
            refs.extend(references(child))
    return refs


def validate_ref(ref: str, spec: YamlObject, canonical_schema: YamlObject) -> str | None:
    if ref.startswith(APPROVED_SCHEMA_REF_ROOT):
        defs = as_object(canonical_schema.get("$defs"), "schema.$defs")
        target = ref.removeprefix(APPROVED_SCHEMA_REF_ROOT)
        if target not in defs:
            return f"missing JSON Schema definition {target!r}"
        return None
    if ref.startswith(COMPONENT_REF_ROOT):
        components = as_object(spec.get("components"), "components")
        section_name, _, target = ref.removeprefix(COMPONENT_REF_ROOT).partition("/")
        section = as_object(components.get(section_name), f"components.{section_name}")
        if target not in section:
            return f"missing OpenAPI component {section_name}/{target}"
        return None
    return f"external ref does not use approved root {APPROVED_SCHEMA_REF_ROOT!r}"


def components_section(spec: YamlObject, name: str) -> YamlObject:
    return as_object(as_object(spec.get("components"), "components").get(name), f"components.{name}")


def resolve_parameter(param: YamlValue, spec: YamlObject, location: str) -> YamlObject:
    param_obj = as_object(param, location)
    ref = param_obj.get("$ref")
    if isinstance(ref, str) and ref.startswith("#/components/parameters/"):
        return as_object(
            components_section(spec, "parameters").get(ref.removeprefix("#/components/parameters/")),
            ref,
        )
    return param_obj


def validate_security_scheme(spec: YamlObject) -> list[CheckFailure]:
    failures: list[CheckFailure] = []
    try:
        schemes = components_section(spec, "securitySchemes")
    except ShapeError:
        return [CheckFailure(OPENAPI_PATH, "components.securitySchemes missing")]
    bearer = schemes.get("bearerAuth")
    if not isinstance(bearer, dict) or bearer.get("type") != "http" or bearer.get("scheme") != "bearer":
        failures.append(CheckFailure(OPENAPI_PATH, "bearerAuth security scheme must be type=http scheme=bearer"))
    global_security = spec.get("security")
    if global_security != [{"bearerAuth": []}]:
        failures.append(CheckFailure(OPENAPI_PATH, "global security must require bearerAuth"))
    return failures


def validate_error_fixtures(spec: YamlObject) -> list[CheckFailure]:
    failures: list[CheckFailure] = []
    try:
        examples = components_section(spec, "examples")
    except ShapeError:
        return [CheckFailure(OPENAPI_PATH, "components.examples missing (auth/policy fixtures required)")]
    expected_fixtures = {
        "MissingAuthError": "unauthorized",
        "PolicyDeniedError": "policy_denied",
        "InvalidPathParameterError": "invalid_path_parameter",
    }
    for fixture_name, expected_code in expected_fixtures.items():
        fixture = examples.get(fixture_name)
        if not isinstance(fixture, dict):
            failures.append(CheckFailure(OPENAPI_PATH, f"missing error fixture components.examples.{fixture_name}"))
            continue
        value = fixture.get("value")
        if not (isinstance(value, dict) and value.get("code") == expected_code and isinstance(value.get("message"), str)):
            failures.append(
                CheckFailure(
                    OPENAPI_PATH,
                    f"fixture {fixture_name} must be an Error payload with code={expected_code!r}",
                )
            )
    return failures


def validate_path_parameters(
    path_name: str, operation_obj: YamlObject, spec: YamlObject
) -> list[CheckFailure]:
    failures: list[CheckFailure] = []
    template_names = PATH_TEMPLATE.findall(path_name)
    parameters = operation_obj.get("parameters")
    declared: dict[str, YamlObject] = {}
    if isinstance(parameters, list):
        for index, param in enumerate(parameters):
            resolved = resolve_parameter(param, spec, f"paths.{path_name}.get.parameters[{index}]")
            if resolved.get("in") == "path":
                declared[as_string(resolved.get("name"), f"{path_name} parameter name")] = resolved
    for template_name in template_names:
        resolved = declared.get(template_name)
        if resolved is None:
            failures.append(CheckFailure(OPENAPI_PATH, f"{path_name} GET missing path parameter {template_name!r}"))
            continue
        if resolved.get("required") is not True:
            failures.append(CheckFailure(OPENAPI_PATH, f"{path_name} path parameter {template_name!r} must be required"))
        schema = resolved.get("schema")
        if not (isinstance(schema, dict) and schema.get("type") == "string" and schema.get("format") == "uuid"):
            failures.append(
                CheckFailure(
                    OPENAPI_PATH,
                    f"{path_name} path parameter {template_name!r} must validate as string/uuid",
                )
            )
    for declared_name in declared:
        if declared_name not in template_names:
            failures.append(
                CheckFailure(OPENAPI_PATH, f"{path_name} declares unknown path parameter {declared_name!r}")
            )
    return failures


def validate_operations(spec: YamlObject) -> list[CheckFailure]:
    paths = as_object(spec.get("paths"), "paths")
    failures: list[CheckFailure] = []
    missing_paths = REQUIRED_PATHS - paths.keys()
    for missing in sorted(missing_paths):
        failures.append(CheckFailure(OPENAPI_PATH, f"missing required path {missing}"))
    for path_name, path_item in paths.items():
        path_obj = as_object(path_item, f"paths.{path_name}")
        for method in ("get", "post", "put", "patch", "delete", "head", "options", "trace"):
            if method not in path_obj:
                continue
            op = as_object(path_obj[method], f"paths.{path_name}.{method}")
            label = f"{path_name} {method.upper()}"
            if op.get("x-implementation") not in ("local-server", "specification-only"):
                failures.append(CheckFailure(OPENAPI_PATH, f"{label} missing implementation classification"))
            if not op.get("operationId"):
                failures.append(CheckFailure(OPENAPI_PATH, f"{label} missing operationId"))
            public = (path_name, method) == ("/health", "get")
            expected_security = [] if public else [{"bearerAuth": []}]
            if op.get("security", spec.get("security")) != expected_security:
                failures.append(CheckFailure(OPENAPI_PATH, f"{label} incorrect security requirement"))
            responses = as_object(op.get("responses"), f"{label}.responses")
            required_statuses = set() if public else set(SECURITY_RESPONSES)
            if not {"200", "201"}.intersection(responses):
                failures.append(CheckFailure(OPENAPI_PATH, f"{label} missing success response"))
            if PATH_TEMPLATE.search(path_name):
                required_statuses |= set(PARAMETERIZED_RESPONSES)
            for status in sorted(required_statuses - responses.keys()):
                failures.append(CheckFailure(OPENAPI_PATH, f"{label} missing {status} response"))
            failures.extend(validate_path_parameters(path_name, op, spec))
    return failures


def validate_openapi() -> list[CheckFailure]:
    spec = as_object(load_yaml(OPENAPI_PATH), "openapi")
    canonical_schema = as_object(load_json(SCHEMA_PATH), "schema")
    failures: list[CheckFailure] = []
    version = as_string(spec.get("openapi"), "openapi")
    if not version.startswith("3.1."):
        failures.append(CheckFailure(OPENAPI_PATH, f"OpenAPI version must be 3.1.x, got {version}"))
    failures.extend(validate_security_scheme(spec))
    failures.extend(validate_error_fixtures(spec))
    failures.extend(validate_operations(spec))
    for ref in references(spec):
        ref_failure = validate_ref(ref, spec, canonical_schema)
        if ref_failure is not None:
            failures.append(CheckFailure(OPENAPI_PATH, f"{ref}: {ref_failure}"))
    return failures


def main() -> int:
    failures = validate_openapi()
    if not failures:
        print("PASS: OpenAPI contract validated")
        return 0
    for failure in failures:
        print(f"FAIL {failure.path.relative_to(ROOT)}: {failure.message}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
