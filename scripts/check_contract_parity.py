#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.13.9"
# dependencies = []
# ///
"""Cross-contract parity checks between the JSON Schema, TypeScript types and SQL DDL.

Compares `schema/mbras.schema.json`, `types/mbras.ts` and `db/schema.sql` under a
contract root and emits deterministic findings with stable IDs and a severity
enum (critical | high | medium | low | info).

Exit code is 1 when any critical/high/medium finding is emitted, 0 otherwise.

Usage:
    uv run scripts/check_contract_parity.py [--root DIR] [--format json|text]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SEVERITIES = ("critical", "high", "medium", "low", "info")
BLOCKING_SEVERITIES = {"critical", "high", "medium"}

SCHEMA_PATH = "schema/mbras.schema.json"
TYPES_PATH = "types/mbras.ts"
SQL_PATH = "db/schema.sql"


def finding(fid: str, severity: str, rule_class: str, message: str, evidence: dict) -> dict:
    assert severity in SEVERITIES
    return {
        "id": fid,
        "severity": severity,
        "rule_class": rule_class,
        "message": message,
        "evidence": evidence,
    }


def extract_sql_table(sql: str, table: str) -> str:
    match = re.search(
        rf"CREATE TABLE {re.escape(table)}\s*\((.*?)\n\);", sql, re.DOTALL
    )
    if not match:
        return ""
    return match.group(1)


def sql_column_line(table_body: str, column: str) -> str:
    for line in table_body.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{column} ") or stripped.startswith(f"{column}\t"):
            return stripped
    return ""


def ts_object_body(ts: str, name: str) -> str:
    match = re.search(
        rf"export const {re.escape(name)} = z\.object\(\{{(.*?)\n\}}\);", ts, re.DOTALL
    )
    if not match:
        return ""
    return match.group(1)


def ts_field_expr(body: str, field: str) -> str:
    match = re.search(rf"^\s*{re.escape(field)}:\s*(.+?),?$", body, re.MULTILINE)
    if not match:
        return ""
    return match.group(1).rstrip(",")


def run_checks(root: Path) -> list[dict]:
    findings: list[dict] = []

    schema_file = root / SCHEMA_PATH
    types_file = root / TYPES_PATH
    sql_file = root / SQL_PATH
    for path in (schema_file, types_file, sql_file):
        if not path.is_file():
            findings.append(
                finding(
                    "PIBRAS-PAR-000",
                    "critical",
                    "parity",
                    f"missing contract file: {path.relative_to(root)}",
                    {"path": str(path.relative_to(root))},
                )
            )
    if findings:
        return findings

    schema = json.loads(schema_file.read_text(encoding="utf-8"))
    ts = types_file.read_text(encoding="utf-8")
    sql = sql_file.read_text(encoding="utf-8")

    defs = schema.get("$defs", {})
    audit = defs.get("AuditEvent", {})
    audit_required = set(audit.get("required", []))
    audit_props = audit.get("properties", {})

    audit_table = extract_sql_table(sql, "audit_log")
    change_type_line = sql_column_line(audit_table, "change_type")
    trust_tier_line = sql_column_line(audit_table, "trust_tier")

    ts_audit = ts_object_body(ts, "AuditEvent")
    ts_change_type = ts_field_expr(ts_audit, "change_type")

    # PIBRAS-PAR-001: change_type required in schema/types but nullable in SQL.
    schema_requires_change_type = "change_type" in audit_required
    ts_requires_change_type = bool(ts_change_type) and ".nullish()" not in ts_change_type and ".optional()" not in ts_change_type
    sql_change_type_not_null = "NOT NULL" in change_type_line
    if schema_requires_change_type and ts_requires_change_type and not sql_change_type_not_null:
        findings.append(
            finding(
                "PIBRAS-PAR-001",
                "high",
                "parity",
                "AuditEvent.change_type is required by schema/mbras.schema.json and "
                "types/mbras.ts but db/schema.sql audit_log.change_type is nullable "
                "(missing NOT NULL)",
                {
                    "schema_required": sorted(audit_required),
                    "sql_column": change_type_line,
                    "ts_field": ts_change_type,
                },
            )
        )

    # PIBRAS-PAR-002: change_type is an enum in schema/types but plain TEXT in SQL.
    schema_change_type_enum = "$ref" in audit_props.get("change_type", {})
    sql_change_type_plain_text = bool(
        re.match(r"change_type\s+TEXT\b", change_type_line)
    )
    if schema_change_type_enum and sql_change_type_plain_text:
        findings.append(
            finding(
                "PIBRAS-PAR-002",
                "medium",
                "parity",
                "AuditEvent.change_type is constrained to the AuditChangeType enum in "
                "schema/mbras.schema.json and types/mbras.ts but db/schema.sql "
                "audit_log.change_type is unconstrained TEXT",
                {
                    "schema_ref": audit_props.get("change_type", {}).get("$ref"),
                    "sql_column": change_type_line,
                },
            )
        )

    # PIBRAS-PAR-003: trust_tier bounded 1..6 in schema but SQL lacks CHECK.
    trust_tier_schema = audit_props.get("trust_tier", {})
    schema_bounds = (
        trust_tier_schema.get("minimum") is not None
        and trust_tier_schema.get("maximum") is not None
    )
    sql_trust_tier_checked = "CHECK" in trust_tier_line
    if schema_bounds and trust_tier_line and not sql_trust_tier_checked:
        findings.append(
            finding(
                "PIBRAS-PAR-003",
                "medium",
                "parity",
                "AuditEvent.trust_tier is bounded (minimum/maximum) in "
                "schema/mbras.schema.json but db/schema.sql audit_log.trust_tier has "
                "no CHECK constraint",
                {
                    "schema_minimum": trust_tier_schema.get("minimum"),
                    "schema_maximum": trust_tier_schema.get("maximum"),
                    "sql_column": trust_tier_line,
                },
            )
        )

    # PIBRAS-PAR-004: exposure_rule.field_visibility NOT NULL in SQL while the
    # JSON Schema neither requires it nor declares a default.
    exposure = defs.get("ExposureRule", {})
    exposure_required = set(exposure.get("required", []))
    exposure_fv = exposure.get("properties", {}).get("field_visibility", {})
    exposure_table = extract_sql_table(sql, "exposure_rule")
    fv_line = sql_column_line(exposure_table, "field_visibility")
    if (
        "NOT NULL" in fv_line
        and "field_visibility" not in exposure_required
        and "default" not in exposure_fv
    ):
        findings.append(
            finding(
                "PIBRAS-PAR-004",
                "medium",
                "parity",
                "exposure_rule.field_visibility is NOT NULL with a default in "
                "db/schema.sql but schema/mbras.schema.json neither requires it nor "
                "declares a default for ExposureRule.field_visibility",
                {
                    "schema_required": sorted(exposure_required),
                    "sql_column": fv_line,
                },
            )
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="contract root directory")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    findings = run_checks(root)
    blocking = [f for f in findings if f["severity"] in BLOCKING_SEVERITIES]

    report = {
        "check": "contract-parity",
        "root": str(root),
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
            print(f"{f['severity'].upper():8s} {f['id']}  {f['message']}")
        print(f"status: {report['status']} ({len(blocking)} blocking findings)")
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
