"""Build a local PIBRAS distribution from immutable Git blobs, or verify its inventory."""

import argparse
import hashlib
import json
import re
import subprocess
import tomllib
import zipfile
from pathlib import Path

MANIFEST = "PACKAGE-MANIFEST.json"
# Public standard kit (not a developer checkout or an npm/PyPI release).
ROOT = {
    "README.md", "GOVERNANCE.md", "RFC_PROCESS.md", "CHANGELOG.md",
    "LICENSE", "LICENSE-CODE", "LICENSE-DOCS", "openapi.yaml",
    "governance/release-policy.yaml", "package.json", "pyproject.toml",
    "scripts/independent_consumer.py", "scripts/public_package.py",
}
DIRS = {"schema", "types", "db", "examples", "mappings", "licenses"}
REQUIRED = {
    "docs/PIBRAS-STANDARD-v0.2.md", "docs/VERSIONING.md", "schema/mbras.schema.json",
    "docs/rfcs/accepted-001-v0.2-reconciliation.md", "licenses/APPLICABILITY.md",
    "licenses/PROVENANCE.json", "tests/golden/conformance-cases.json",
    "types/mbras.ts", "db/schema.sql", "examples/property.sample.json",
} | (ROOT - {"CHANGELOG.md"})


def public(path):
    return (path in ROOT or path.split("/")[0] in DIRS
            or path.startswith("tests/golden/")
            or (path.startswith("docs/") and path.endswith(".md")
                and not path.startswith("docs/plans/")))


def license_for(path):
    if path in {"LICENSE", "LICENSE-CODE", "LICENSE-DOCS"}:
        return "not-applicable"
    if path.endswith(".md") and not path.startswith("licenses/"):
        return "CC-BY-4.0"
    return "Apache-2.0"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(["git", *args])


def inventory(files, commit):
    if not REQUIRED <= files.keys():
        raise ValueError(f"missing distribution inputs: {sorted(REQUIRED - files.keys())}")
    provenance = json.loads(files["licenses/PROVENANCE.json"])["licences"]
    mirrors = {"Apache-2.0": "LICENSE-CODE", "CC-BY-4.0": "LICENSE-DOCS"}
    if {row["id"] for row in provenance} != set(mirrors):
        raise ValueError("unexpected licence provenance")
    for row in provenance:
        original = files[row["file"]]
        if sha(original) != row["sha256"] or original != files[mirrors[row["id"]]]:
            raise ValueError(f"licence provenance mismatch: {row['id']}")
    info_version = re.search(rb"(?m)^  version: ([^\r\n]+)$", files["openapi.yaml"])
    if not info_version:
        raise ValueError("missing OpenAPI info.version")
    return {
        "format": 1, "status": "local-rehearsal-unsigned", "git_commit": commit,
        "versions": {
            "standard": "v0.2",
            "schema": json.loads(files["schema/mbras.schema.json"])["version"],
            "openapi_info": info_version[1].decode().strip("\"'"),
            "node_project": json.loads(files["package.json"])["version"],
            "python_project": tomllib.loads(files["pyproject.toml"].decode())["project"]["version"],
        },
        "files": {p: {"sha256": sha(data), "license": license_for(p)}
                  for p, data in sorted(files.items())},
    }


def manifest_bytes(files, commit):
    return (json.dumps(inventory(files, commit), indent=2, sort_keys=True) + "\n").encode()


def build(rev, output):
    commit = git("rev-parse", "--verify", "--end-of-options", rev + "^{commit}").decode().strip()
    files = {}
    for entry in git("ls-tree", "-rz", "--full-tree", commit).split(b"\0"):
        if not entry:
            continue
        meta, rawpath = entry.split(b"\t", 1)
        path = rawpath.decode()
        if not public(path):
            continue
        mode, kind, oid = meta.decode().split()
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError(f"not a regular Git file: {path}")
        files[path] = git("cat-file", "blob", oid)
    files[MANIFEST] = manifest_bytes(files, commit)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_STORED) as archive:
        for path, data in sorted(files.items()):
            info = zipfile.ZipInfo(path, (1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)
    print(f"{sha(output.read_bytes())}  {output}  git:{commit}")


def verify(root):
    files = {}
    for file in root.rglob("*"):
        if file.is_symlink() or not (file.is_file() or file.is_dir()):
            raise ValueError(f"unexpected file type: {file}")
        if file.is_file():
            path = file.relative_to(root).as_posix()
            if path != MANIFEST and not public(path):
                raise ValueError(f"unexpected distribution entry: {path}")
            files[path] = file.read_bytes()
    manifest = files.pop(MANIFEST)
    record = json.loads(manifest)
    commit = record["git_commit"]
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
        raise ValueError("invalid source commit")
    if manifest_bytes(files, commit) != manifest:
        raise ValueError("inventory mismatch: content, metadata or membership changed")
    print(f"verified {len(files)} files from git:{commit} (unsigned)")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    builder = modes.add_parser("build")
    builder.add_argument("revision")
    builder.add_argument("output", type=Path)
    modes.add_parser("verify").add_argument("root", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "build":
            build(args.revision, args.output)
        else:
            verify(args.root)
    except (KeyError, OSError, ValueError, TypeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"package check failed: {exc}\n")


if __name__ == "__main__":
    main()
