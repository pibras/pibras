#!/usr/bin/env python3
"""validate_release_policy.py — validate governance/release-policy.yaml against schema/release-policy.schema.json."""
import json, sys, pathlib

try:
    import yaml
except ImportError:
    yaml = None
try:
    import jsonschema
except ImportError:
    jsonschema = None

def load_yaml(path):
    if yaml:
        return yaml.safe_load(pathlib.Path(path).read_text())
    raise SystemExit("pyyaml required (uv run --with pyyaml --with jsonschema)")

def main():
    # CI já passa o caminho como argumento; antes ele era ignorado e o
    # validador sempre lia o arquivo commitado, tornando impossível validar
    # uma política candidata.
    path = sys.argv[1] if len(sys.argv) > 1 else "governance/release-policy.yaml"
    doc = load_yaml(path)
    schema = json.loads(pathlib.Path("schema/release-policy.schema.json").read_text())
    if jsonschema is None:
        raise SystemExit("jsonschema required (uv run --with pyyaml --with jsonschema)")
    v = jsonschema.Draft202012Validator(schema)
    errors = sorted(v.iter_errors(doc), key=lambda e: list(e.path))

    # JSON Schema requires the approval but cannot express reviewability: the
    # plan requires an approver with an immutable review reference, so the
    # reference-presence rule is enforced in code rather than left as
    # documentation. (Distinctness across multiple approvers is not required
    # while the project has a single maintainer; revisit if the maintainer
    # group grows.)
    approvals = doc.get("approvals") or []
    if doc.get("phase") in {"rfc_accepted", "legal_approved", "rc", "final"}:
        rfc_approvals = [a for a in approvals if a.get("gate") == "rfc"]
        if not any(a.get("approver") and a.get("review_reference") for a in rfc_approvals):
            print(
                "RELEASE POLICY INVALID\n  approvals: rfc gate needs at least one "
                "approval with approver and immutable review_reference",
                file=sys.stderr,
            )
            return 1

    if errors:
        print("RELEASE POLICY INVALID", file=sys.stderr)
        for e in errors:
            print(f"  {'/'.join(map(str, e.path)) or '<root>'}: {e.message}", file=sys.stderr)
        return 1
    print(f"release policy OK (phase={doc['phase']}, approvals={len(doc['approvals'])})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
