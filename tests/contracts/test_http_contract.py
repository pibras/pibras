"""Exercise the two published surfaces without assuming a deployed API."""
import json
import os
import re
import secrets
import select
import subprocess
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import UUID

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[2]
SPEC = yaml.safe_load((ROOT / "openapi.yaml").read_text())
CANON = json.loads((ROOT / "schema/mbras.schema.json").read_text())
BASE = "https://contract.invalid/openapi.yaml"
REGISTRY = Registry().with_resources([
    (BASE, Resource.from_contents(SPEC, default_specification=DRAFT202012)),
    ("https://contract.invalid/schema/mbras.schema.json", Resource.from_contents(CANON)),
])
PROP = json.loads((ROOT / "tests/golden/property.valid.json").read_text())["payload"]
DENY = {**json.loads((ROOT / "tests/golden/exposure-policy.default-deny.json").read_text())["payload"],
        "resource_id": PROP["id"], "rules": [], "default_decision": "deny"}
UNIT = {"id": PROP["unit_id"], "property_type": "apartment", "provenance": PROP["provenance"],
        "audit": PROP["audit"], "address": {}, "dedupe_key": "demo", "normalized_address_key": "demo"}
CASES = {
    ("get", "/health"): (None, 200),
    ("post", "/api/v1/ingest/raw"): ({"source_system": "kenlo", "payload": {"codigo": "demo"}}, 201),
    ("post", "/api/v1/ingest/csv-row"): ({"row": {"rua": "Rua Exemplo", "valor": 100}}, 201),
    ("post", "/api/v1/ingest/kenlo"): ({"codigo": "demo"}, 201),
    ("post", "/api/v1/ingest/zap-xml"): ({"xml_item": "<Listing><ListingID>demo</ListingID></Listing>"}, 201),
    ("post", "/api/v1/dedupe/match"): ({"incoming_unit": UNIT, "existing_inventory": []}, 200),
    ("post", "/api/v1/survivorship/arbitrate"): ({"entity_type": "property", "entity_id": None,
        "current_data": None, "current_trust_tier": None, "incoming_data": {"code": "demo"},
        "incoming_source": "kenlo", "incoming_trust_tier": 3}, 200),
    ("post", "/api/v1/policy/project"): ({"property": PROP, "policy": DENY, "channel_type": "portal",
                                          "caller_role": "portal_feed"}, 200),
    ("post", "/api/v1/crm/twenty/from"): ({"payload": {"code": "demo"}, "currentProperty": None,
                                         "currentUnit": None}, 200),
    ("post", "/api/v1/feeds/portal"): ({"items": [{"property": PROP, "policy": DENY}]}, 200),
}


@pytest.fixture(scope="module")
def server():
    token = secrets.token_hex(24)
    # Let the OS reserve the port atomically; publish it only after listening.
    script = """
    import {createPibrasApiServer} from './src/api/server.ts';
    const server = createPibrasApiServer();
    server.listen(0, '127.0.0.1', () => console.log(server.address().port));
    """
    with subprocess.Popen(["node", "--experimental-strip-types", "--input-type=module", "-e", script],
                          cwd=ROOT, env={**os.environ, "PIBRAS_API_TOKEN": token},
                          stdout=subprocess.PIPE, text=True) as proc:
        try:
            assert select.select([proc.stdout], [], [], 20)[0], "Node server startup timed out"
            port = int(proc.stdout.readline())
            yield f"http://127.0.0.1:{port}", token
        finally:
            proc.terminate()


def request(server, method, path, payload=None, token=None):
    req = urllib.request.Request(server[0] + path, method=method.upper())
    if payload is not None:
        req.data = json.dumps(payload).encode()
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        response = urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as exc:
        response = exc
    with response:
        return response.status, response.headers.get_content_type(), response.read()


def validate_schema(schema, data):
    # Bind component fragments and external schema references to an offline registry.
    Draft202012Validator({"$id": BASE, "components": SPEC["components"], **schema},
                         registry=REGISTRY, format_checker=FormatChecker()).validate(data)


def validate_response(op, status, media, data):
    response = op["responses"][str(status)]
    if "$ref" in response:
        response = SPEC["components"]["responses"][response["$ref"].split("/")[-1]]
    schema = response["content"][media]["schema"]
    payload = json.loads(data) if media == "application/json" else data.decode()
    validate_schema(schema, payload)
    return payload


def test_local_coverage():
    assert {(method, path) for path, item in SPEC["paths"].items() for method, op in item.items()
            if op["x-implementation"] == "local-server"} == CASES.keys()


def test_all_declared_server_routes_are_exercised():
    # The reference server dispatches on literal path/method pairs. If dispatch
    # moves to a router, enumerate that router instead of dropping the check.
    source = (ROOT / "src/api/server.ts").read_text()
    routes = re.findall(r'url\.pathname\s*===\s*"([^"]+)"\s*&&\s*method\s*===\s*"([A-Z]+)"', source)
    assert {(method.lower(), path) for path, method in routes} == CASES.keys()


def test_domain_schema_bindings():
    schemas = SPEC["components"]["schemas"]
    for name in ("Unit", "Property", "ExposurePolicy", "Listing"):
        assert schemas[name] == {"$ref": f"./schema/mbras.schema.json#/$defs/{name}"}
    for field, name in (("unit", "Unit"), ("property", "Property")):
        assert schemas["CsvBundle"]["properties"][field] == {"$ref": f"#/components/schemas/{name}"}
    assert schemas["ProjectionInput"]["properties"]["policy"] == {"$ref": "#/components/schemas/ExposurePolicy"}


@pytest.mark.parametrize(("method", "path"), CASES)
def test_live_operation(server, method, path):
    op = SPEC["paths"][path][method]
    payload, expected = CASES[method, path]
    if method == "post":
        validate_schema(op["requestBody"]["content"]["application/json"]["schema"], payload)
        for credential, denied in [(None, 401), ("invalid", 403)]:
            status, media, data = request(server, method, path, payload, credential)
            assert (status, media) == (denied, "application/json")
            assert set(validate_response(op, status, media, data)) == {"success", "error"}
    status, media, data = request(server, method, path, payload, server[1] if method == "post" else None)
    assert status == expected
    result = validate_response(op, status, media, data)
    if path.endswith("/policy/project"):
        projected = result["data"]
        if projected is not None:
            assert projected["evaluation"]["decision"] == "deny"
            assert (projected["property"], projected["unit"], projected["media_assets"]) == ({}, None, [])
    if path.endswith("/feeds/portal"):
        root = ET.fromstring(result)
        assert root.tag == "Listings" and len(root) == 0


@pytest.mark.parametrize(("method", "path"), [(method, path) for path, item in SPEC["paths"].items()
    for method, op in item.items() if op["x-implementation"] == "specification-only"])
def test_reference_operation_not_served(server, method, path):
    for parameter in ("unit_id", "property_id", "listing_id"):
        path = path.replace("{" + parameter + "}", str(UUID(int=1)))
    assert request(server, method, path, token=server[1])[0] == 404
