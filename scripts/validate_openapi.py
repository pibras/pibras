#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pyyaml",
# ]
# ///

# How to run
# 1. Install uv (if not installed):
#      curl -LsSf https://astral.sh/uv/install.sh | sh
# 2. Run directly (no venv, no pip install needed):
#      uv run scripts/validate_openapi.py
# 3. Or make executable and run:
#      chmod +x scripts/validate_openapi.py && ./scripts/validate_openapi.py

from __future__ import annotations

import json
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
REQUIRED_PATHS: Final = frozenset(("/units/{unit_id}", "/properties/{property_id}", "/listings/{listing_id}"))


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
    schema_prefix = "./schema/mbras.schema.json#/$defs/"
    component_prefix = "#/components/schemas/"
    if ref.startswith(schema_prefix):
        defs = as_object(canonical_schema.get("$defs"), "schema.$defs")
        target = ref.removeprefix(schema_prefix)
        if target not in defs:
            return f"missing JSON Schema definition {target!r}"
        return None
    if ref.startswith(component_prefix):
        schemas = as_object(as_object(spec.get("components"), "components").get("schemas"), "components.schemas")
        target = ref.removeprefix(component_prefix)
        if target not in schemas:
            return f"missing OpenAPI component schema {target!r}"
        return None
    return None


def validate_operations(spec: YamlObject) -> list[CheckFailure]:
    paths = as_object(spec.get("paths"), "paths")
    failures: list[CheckFailure] = []
    missing_paths = REQUIRED_PATHS - paths.keys()
    for missing in sorted(missing_paths):
        failures.append(CheckFailure(OPENAPI_PATH, f"missing required path {missing}"))
    for path_name, path_item in paths.items():
        path_obj = as_object(path_item, f"paths.{path_name}")
        operation = path_obj.get("get")
        if operation is None:
            continue
        operation_obj = as_object(operation, f"paths.{path_name}.get")
        if operation_obj.get("operationId") is None:
            failures.append(CheckFailure(OPENAPI_PATH, f"{path_name} GET missing operationId"))
        responses = as_object(operation_obj.get("responses"), f"paths.{path_name}.get.responses")
        if "200" not in responses:
            failures.append(CheckFailure(OPENAPI_PATH, f"{path_name} GET missing 200 response"))
    return failures


def validate_openapi() -> list[CheckFailure]:
    spec = as_object(load_yaml(OPENAPI_PATH), "openapi")
    canonical_schema = as_object(load_json(SCHEMA_PATH), "schema")
    failures: list[CheckFailure] = []
    version = as_string(spec.get("openapi"), "openapi")
    if not version.startswith("3.1."):
        failures.append(CheckFailure(OPENAPI_PATH, f"OpenAPI version must be 3.1.x, got {version}"))
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
