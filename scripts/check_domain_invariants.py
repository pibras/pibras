#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.13.9"
# dependencies = []
# ///
"""Domain-invariant checks over entity datasets (cross-entity integrity).

Reads `buildings.json`, `units.json` and `properties.json` from an entity
directory and verifies cross-entity invariants, e.g. that a Property's
`building_id` matches the `building_id` of its Unit.

Findings use the same stable-ID + severity model as the parity checker
(critical | high | medium | low | info). Findings with rule_class
"identity" (dedupe/physical-identity rules) are reported but NEVER counted
as blocking: identity reconciliation is out of scope for these gates.

Exit code is 1 when any non-identity critical/high/medium finding is
emitted, 0 otherwise.

Usage:
    uv run scripts/check_domain_invariants.py --entities DIR [--format json|text]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SEVERITIES = ("critical", "high", "medium", "low", "info")
BLOCKING_SEVERITIES = {"critical", "high", "medium"}


def finding(fid: str, severity: str, rule_class: str, message: str, evidence: dict) -> dict:
    assert severity in SEVERITIES
    return {
        "id": fid,
        "severity": severity,
        "rule_class": rule_class,
        "message": message,
        "evidence": evidence,
    }


def load(entities_dir: Path, name: str) -> list[dict]:
    path = entities_dir / f"{name}.json"
    if not path.is_file():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def run_checks(entities_dir: Path) -> list[dict]:
    findings: list[dict] = []
    buildings = {b["id"]: b for b in load(entities_dir, "buildings")}
    units = {u["id"]: u for u in load(entities_dir, "units")}
    properties = {p["id"]: p for p in load(entities_dir, "properties")}

    for pid in sorted(properties):
        prop = properties[pid]
        unit_id = prop.get("unit_id")
        unit = units.get(unit_id)

        # PIBRAS-INV-001: Property must reference an existing Unit.
        if unit is None:
            findings.append(
                finding(
                    "PIBRAS-INV-001",
                    "critical",
                    "invariant",
                    f"Property {pid} references unit_id {unit_id} which does not exist",
                    {"property_id": pid, "unit_id": unit_id},
                )
            )
            continue

        # PIBRAS-INV-002: Property.building_id must match its Unit.building_id.
        if prop.get("building_id") != unit.get("building_id"):
            findings.append(
                finding(
                    "PIBRAS-INV-002",
                    "high",
                    "invariant",
                    f"Property {pid} has building_id {prop.get('building_id')} but its "
                    f"Unit {unit_id} has building_id {unit.get('building_id')}",
                    {
                        "property_id": pid,
                        "property_building_id": prop.get("building_id"),
                        "unit_id": unit_id,
                        "unit_building_id": unit.get("building_id"),
                    },
                )
            )

    for uid in sorted(units):
        unit = units[uid]
        building_id = unit.get("building_id")

        # PIBRAS-INV-003: Unit.building_id, when set, must reference an existing Building.
        if building_id is not None and building_id not in buildings:
            findings.append(
                finding(
                    "PIBRAS-INV-003",
                    "medium",
                    "invariant",
                    f"Unit {uid} references building_id {building_id} which does not exist",
                    {"unit_id": uid, "building_id": building_id},
                )
            )

        # PIBRAS-IDN-001 (identity rule — excluded from blocking/manifest):
        # duplicate_of_unit_id must reference an existing, distinct Unit.
        dup = unit.get("duplicate_of_unit_id")
        if dup is not None and (dup == uid or dup not in units):
            findings.append(
                finding(
                    "PIBRAS-IDN-001",
                    "medium",
                    "identity",
                    f"Unit {uid} has duplicate_of_unit_id {dup} which is dangling or "
                    "self-referential (identity rule, excluded from gates)",
                    {"unit_id": uid, "duplicate_of_unit_id": dup},
                )
            )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entities", required=True, help="entity fixture directory")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args()

    entities_dir = Path(args.entities).resolve()
    findings = run_checks(entities_dir)
    blocking = [
        f
        for f in findings
        if f["severity"] in BLOCKING_SEVERITIES and f["rule_class"] != "identity"
    ]

    report = {
        "check": "domain-invariants",
        "entities": str(entities_dir),
        "severity_enum": list(SEVERITIES),
        "findings": findings,
        "blocking_count": len(blocking),
        "status": "red" if blocking else "green",
    }
    if args.format == "json":
        json.dump(report, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
    else:
        for f in findings:
            print(f"{f['severity'].upper():8s} {f['id']}  [{f['rule_class']}] {f['message']}")
        print(f"status: {report['status']} ({len(blocking)} blocking findings)")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
