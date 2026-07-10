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
    doc = load_yaml("governance/release-policy.yaml")
    schema = json.loads(pathlib.Path("schema/release-policy.schema.json").read_text())
    if jsonschema is None:
        raise SystemExit("jsonschema required (uv run --with pyyaml --with jsonschema)")
    v = jsonschema.Draft202012Validator(schema)
    errors = sorted(v.iter_errors(doc), key=lambda e: list(e.path))
    if errors:
        print("RELEASE POLICY INVALID", file=sys.stderr)
        for e in errors:
            print(f"  {'/'.join(map(str, e.path)) or '<root>'}: {e.message}", file=sys.stderr)
        return 1
    print(f"release policy OK (phase={doc['phase']}, approvals={len(doc['approvals'])})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
