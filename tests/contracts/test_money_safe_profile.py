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
