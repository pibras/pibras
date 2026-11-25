import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[2]
LIMIT = 2**53 - 1


def test_profile_and_base_share_the_wire_cases():
    base = json.loads((ROOT / "schema/mbras.schema.json").read_text())
    profile = json.loads((ROOT / "schema/profiles/money-safe-v1.json").read_text())
    registry = Registry().with_resource(base["$id"], Resource.from_contents(base))
    legacy = Draft202012Validator({"$ref": base["$id"] + "#/$defs/Money"}, registry=registry)
    validator = Draft202012Validator(profile, registry=registry)
    cases = [
        ({"amount": amount, "currency": "BRL"}, accepted, legacy_ok)
        for amount, accepted, legacy_ok in [
            (-LIMIT-1, False, True), (-LIMIT, True, True), (-1, True, True),
            (0, True, True), (LIMIT, True, True), (LIMIT+1, False, True),
            (0.5, False, False), ("1", False, False),
        ]
    ] + [({"amount": 0, "currency": "INVALID"}, False, False),
         ({"amount": 0, "currency": "BRL", "extra": True}, False, False)]
    rows = [{"entity": "SafeMoney", "id": str(i), "input": obj}
            for i, (obj, _, _) in enumerate(cases)]
    result = subprocess.run(
        ["node", "--experimental-strip-types", "scripts/evaluate_zod.ts",
         str(ROOT / "types/profiles/money-safe-v1.ts")],
        cwd=ROOT, input=json.dumps(rows), capture_output=True, text=True, check=True,
    )
    outputs = json.loads(result.stdout)
    assert len(outputs) == len(cases)
    for i, (obj, accepted, legacy_ok) in enumerate(cases):
        assert outputs[i]["id"] == str(i)
        assert outputs[i]["valid"] == validator.is_valid(obj) == accepted
        assert legacy.is_valid(obj) == legacy_ok


def test_exact_wire_numbers_are_validated_before_rounding():
    from decimal import Decimal

    base = json.loads((ROOT / "schema/mbras.schema.json").read_text())
    profile = json.loads((ROOT / "schema/profiles/money-safe-v1.json").read_text())
    registry = Registry().with_resource(base["$id"], Resource.from_contents(base))
    validator = Draft202012Validator(profile, registry=registry)

    def exact(token):
        value = Decimal(token)
        return int(value) if value == value.to_integral_value() else value

    cases = [
        ("9007199254740990.5", False), ("-9007199254740990.5", False),
        ("9007199254740991.0000000001", False), ("1e-400", False),
        ("9007199254740992", False), ("-9007199254740992", False),
        ("90071992547409910e-1", True), ("-9007199254740991.0", True),
        ("1.200e1", True), ("-0e400", True), ("1e400", False),
        ('"1"', False), ("true", False),
    ]
    raw = ['{"currency":"BRL","amount":' + token + '}' for token, _ in cases]
    reader = """
        import { parseSafeMoneyJson } from './types/profiles/money-safe-v1.ts';
        import { readFileSync } from 'node:fs';
        console.log(JSON.stringify(JSON.parse(readFileSync(0,'utf8')).map(raw => {
            try { return parseSafeMoneyJson(raw).amount; } catch { return null; }
        })));
    """
    result = subprocess.run(["node", "--experimental-strip-types", "--input-type=module",
                             "-e", reader], cwd=ROOT, input=json.dumps(raw), text=True,
                            capture_output=True, check=True)
    for wire, (_, expected), amount in zip(raw, cases, json.loads(result.stdout), strict=True):
        obj = json.loads(wire, parse_float=exact)
        assert validator.is_valid(obj) == expected, wire
        assert amount == (obj["amount"] if expected else None), wire
