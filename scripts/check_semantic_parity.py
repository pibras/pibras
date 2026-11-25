"""Run one corpus through Draft 2020-12 (with formats) and canonical Zod exports.

uv run --frozen python scripts/check_semantic_parity.py [--root CONTRACT_ROOT]
The corpus stays fixed when --root points at a mutated candidate.
"""
import argparse
import json
from pathlib import Path
import subprocess

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def corpus():
    rows = json.loads((ROOT / "tests/contracts/semantic-cases.json").read_text())
    data = json.loads((ROOT / "tests/golden/ownership-compatibility.json").read_text())["entities"]

    def add(name, entity, value, expected=True):
        rows.append({"id": name, "entity": entity, "input": value, "expected": expected})

    for entity, key in (("Owner", "ownerA"), ("Party", "partyA"),
                        ("Ownership", "propertyOwnershipA"), ("Ownership", "propertyOwnershipB"),
                        ("Ownership", "unitOwnershipA")):
        add("migration." + key, entity, data[key])
    ownership = data["propertyOwnershipA"]
    add("ownership.other-null", "Ownership", ownership | {"unit_id": None})
    add("ownership.both", "Ownership", ownership | {"unit_id": data["unitA"]}, False)
    add("ownership.neither", "Ownership", {k: v for k, v in ownership.items() if k != "property_id"}, False)
    add("ownership.both-null", "Ownership", ownership | {"property_id": None, "unit_id": None}, False)
    add("ownership.party-missing", "Ownership", {k: v for k, v in ownership.items() if k != "party_id"}, False)
    def golden(filename):
        return json.loads((ROOT / "tests/golden" / filename).read_text())["payload"]

    propagation = golden("dsar-propagation.fulfilled.json")
    add("dsar.propagation.fulfilled", "DSARPropagation", propagation)
    for label, ref in (("null", None), ("empty", ""), ("blank", "  ")):
        add("dsar.propagation.evidence-" + label, "DSARPropagation", propagation | {"evidence_ref": ref}, False)
    no_ref = {k: v for k, v in propagation.items() if k != "evidence_ref"}
    add("dsar.propagation.evidence-missing", "DSARPropagation", no_ref, False)
    add("dsar.propagation.pending", "DSARPropagation", no_ref | {"status": "pending", "fulfilled_at": None})
    deletion = golden("data-subject-request.deletion-fulfilled.json")
    add("dsar.deletion.fulfilled", "DataSubjectRequest", deletion)
    for field, bad in (("resolution_action", None), ("affected_record_ids", [])):
        add("dsar.deletion.invalid-" + field, "DataSubjectRequest", deletion | {field: bad}, False)
        add("dsar.deletion.missing-" + field, "DataSubjectRequest",
            {k: v for k, v in deletion.items() if k != field}, False)
    no_effect = {k: v for k, v in deletion.items() if k not in ("resolution_action", "affected_record_ids")}
    add("dsar.deletion.in-progress", "DataSubjectRequest", no_effect | {"status": "in_progress", "fulfilled_at": None})
    add("dsar.access.fulfilled", "DataSubjectRequest", no_effect | {"request_type": "access"})
    return rows


def evaluate(root):
    schema = json.loads((root / "schema/mbras.schema.json").read_text())
    Draft202012Validator.check_schema(schema)
    rows = corpus()
    # Observations are not parity passes or a normative exception. A change in
    # either runtime must be reviewed before removing the promotion blocker.
    observations = json.loads((ROOT / "tests/contracts/compatibility-observations.json").read_text())
    rows.extend(observations)
    inputs = [{k: row[k] for k in ("id", "entity", "input")} for row in rows]
    proc = subprocess.run(
        ["node", "--experimental-strip-types", str(ROOT / "scripts/evaluate_zod.ts"),
         str(root / "types/mbras.ts")],
        input=json.dumps(inputs), capture_output=True, text=True,
    )
    if proc.returncode:
        raise RuntimeError(f"Zod runtime failed: {proc.stderr}")
    zod = json.loads(proc.stdout)
    results = []
    compatibility = []
    for row, observed in zip(rows, zod, strict=True):
        if observed["id"] != row["id"]:
            raise ValueError("misaligned Zod results")
        entity = row["entity"]
        validator = Draft202012Validator(
            {**schema, "$ref": f"#/$defs/{entity}"},
            format_checker=Draft202012Validator.FORMAT_CHECKER,
        )
        valid = validator.is_valid(row["input"])
        expected = row["expected"]
        errors = []
        if valid != (expected["json_schema"] if "decision" in row else expected):
            errors.append("json_schema.acceptance")
        if observed["valid"] != (expected["zod"] if "decision" in row else expected):
            errors.append("zod.acceptance")
        # JSON Schema annotates defaults, whereas Zod materializes them.
        # Check both against the same expected value, not against each other.
        fields = schema["$defs"][entity].get("properties", {})
        for field, value in row.get("defaults", {}).items():
            if json.dumps(fields[field].get("default")) != json.dumps(value):
                errors.append(f"json_schema.default.{field}")
            if json.dumps((observed["output"] or {}).get(field)) != json.dumps(value):
                errors.append(f"zod.default.{field}")
        if expected and observed["valid"]:
            # Transforms/defaults must not overwrite explicitly supplied fields.
            for key, value in row["input"].items():
                # Nested objects may legitimately acquire additional defaults.
                if not isinstance(value, (dict, list)) and json.dumps(observed["output"].get(key)) != json.dumps(value):
                    errors.append(f"zod.output.{key}")
        result = {"id": row["id"], "expected": expected, "json_schema": valid,
                  "zod": observed["valid"], "errors": errors}
        if "decision" in row:
            compatibility.append(result | {"decision": row["decision"]})
        else:
            results.append(result)
    red = any(r["errors"] for r in results + compatibility)
    return {"status": "red" if red else "green", "rows": results,
            "compatibility_observations": compatibility}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    result = evaluate(parser.parse_args().root.resolve())
    print(json.dumps(result, indent=2))
    raise SystemExit(result["status"] != "green")
