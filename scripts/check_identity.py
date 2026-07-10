#!/usr/bin/env python3
"""check_identity.py — fail if branded uppercase tokens appear outside exempt paths."""
import re, subprocess, sys, pathlib

# Token assembled from fragments so this scanner does not flag itself.
TOKEN = re.compile("MB" + "RAS")
BANNER = "Status: historical and non-authoritative"

def exempt_paths():
    text = pathlib.Path("governance/release-policy.yaml").read_text()
    paths, in_block = [], False
    for line in text.splitlines():
        if line.strip() == "brand_exempt_paths:":
            in_block = True; continue
        if in_block:
            s = line.strip()
            if s.startswith("- "):
                paths.append(s[2:].strip())
            else:
                break
    return set(paths)

def main():
    exempt = exempt_paths()
    files = subprocess.run(["git", "ls-files"], capture_output=True, text=True, check=True).stdout.split()
    failures = []
    for f in files:
        p = pathlib.Path(f)
        if not p.is_file():
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, FileNotFoundError, IsADirectoryError):
            continue
        if f in exempt:
            head = "\n".join(text.splitlines()[:20])
            if BANNER not in head:
                failures.append(f"{f}: exempt file missing banner '{BANNER}'")
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if TOKEN.search(line):
                failures.append(f"{f}:{i}: branded token: {line.strip()[:100]}")
    if failures:
        print("IDENTITY CHECK FAILED", file=sys.stderr)
        for x in failures:
            print("  " + x, file=sys.stderr)
        return 1
    print(f"identity check OK ({len(files)} files, {len(exempt)} exempt)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
