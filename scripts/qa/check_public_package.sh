#!/usr/bin/env bash
# Run from a checkout after frozen Python bootstrap.
set -eu
cd "$(dirname "$0")/../.."
python="$PWD/.venv/bin/python"
sha=$(git rev-parse HEAD)
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
for name in first second; do
  "$python" scripts/public_package.py build "$sha" "$tmp/$name.zip"
done
cmp "$tmp/first.zip" "$tmp/second.zip"
"$python" -m zipfile -e "$tmp/first.zip" "$tmp/kit"
cd "$tmp/kit"
"$python" scripts/public_package.py verify .
"$python" -B scripts/independent_consumer.py
printf ' ' >>examples/property.sample.json
if "$python" scripts/public_package.py verify .; then
  echo "Expected changed package content to fail verification" >&2
  exit 1
fi
echo "Package reproduction, consumer and tamper checks passed for $sha"
