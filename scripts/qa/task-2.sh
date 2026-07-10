#!/usr/bin/env bash
# QA for Todo 2: Lock Python and TypeScript toolchains and canonical commands.
# Usage: scripts/qa/task-2.sh --report .omo/evidence/task-2-manifest.json
set -euo pipefail

REPORT=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --report) REPORT="$2"; shift 2 ;;
    *) echo "unknown arg: $1" >&2; exit 2 ;;
  esac
done
[[ -n "$REPORT" ]] || { echo "--report is required" >&2; exit 2; }

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

EVIDENCE_DIR="$(dirname "$REPORT")"
mkdir -p "$EVIDENCE_DIR"
FAILURES=()
COMMANDS_LOG="$EVIDENCE_DIR/task-2-commands.log"
QA_SUMMARY="$EVIDENCE_DIR/task-2-qa-summary.json"
TYPE_MANIFEST="$EVIDENCE_DIR/task-2-types-manifest.json"
: > "$COMMANDS_LOG"

record_failure() {
  local name="$1"
  FAILURES+=("$name")
  echo "FAIL  $name"
}

run_ok() {
  local name="$1"
  shift
  local log="$EVIDENCE_DIR/task-2-$name.log"
  printf '$ %q' "$@" > "$log"
  printf '\n' >> "$log"
  printf '%s\t%s\n' "$name" "$*" >> "$COMMANDS_LOG"
  if "$@" >> "$log" 2>&1; then
    echo "PASS  $name"
  else
    record_failure "$name"
  fi
}

run_shell_ok() {
  local name="$1"
  local command="$2"
  run_ok "$name" bash -lc "$command"
}

run_shell_fails() {
  local name="$1"
  local command="$2"
  local log="$EVIDENCE_DIR/task-2-$name.log"
  printf '$ bash -lc %q\n' "$command" > "$log"
  printf '%s\t%s\n' "$name" "$command" >> "$COMMANDS_LOG"
  if bash -lc "$command" >> "$log" 2>&1; then
    record_failure "$name"
  else
    echo "PASS  $name"
  fi
}

run_ok "npm-view-typescript" npm view typescript@7.0.2 version
run_ok "npm-view-zod" npm view zod@4.4.3 version
run_shell_ok "uv-version" "test \"\$(uv --version)\" = \"uv 0.9.7 (0adb44480 2025-10-30)\""
run_shell_ok "python-version" "test \"\$(uv run python -c 'import sys; print(\".\".join(map(str, sys.version_info[:3])))')\" = \"3.13.9\""
run_shell_ok "node-version" "test \"\$(node --version)\" = \"v22.22.3\""
run_shell_ok "npm-version" "test \"\$(npm --version)\" = \"10.9.8\""
run_ok "uv-lock-check" uv lock --check
run_ok "uv-sync-frozen" uv sync --frozen
run_ok "npm-ci" npm ci
run_ok "npm-typecheck" npm run typecheck
run_ok "npm-test-types-1" npm run test:types
run_ok "npm-test-types-2" npm run test:types
run_ok "types-manifest" npm run export:types-manifest -- --out "$TYPE_MANIFEST"
run_ok "validate-conformance" uv run scripts/validate_conformance.py
run_ok "validate-openapi" uv run scripts/validate_openapi.py
run_ok "openapi-spec-validator" uv run openapi-spec-validator openapi.yaml
run_ok "shellcheck-version" uv run shellcheck --version
run_ok "pip-audit-version" uv run pip-audit --version
run_ok "detect-secrets-version" uv run detect-secrets --version
run_ok "openapi-spec-validator-version" uv run openapi-spec-validator --version
run_ok "shellcheck-task-2" uv run shellcheck scripts/qa/task-2.sh

run_shell_ok "readme-assertion" 'grep -F "uv sync --frozen" README.md && grep -F "npm ci" README.md && grep -F "npm run typecheck" README.md && grep -F "npm run test:types" README.md && grep -F "scripts/qa/task-2.sh --report .omo/evidence/task-2-manifest.json" README.md'

TMP="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP"
}
trap cleanup EXIT

BRANCH="$(git branch --show-current)"
CLONE="$TMP/clean"
run_ok "clean-clone" git clone -q --branch "$BRANCH" "$ROOT" "$CLONE"
run_shell_ok "clean-clone-checks" 'cd "'"$CLONE"'" && uv sync --frozen && npm ci && npm run typecheck && npm run test:types && uv run scripts/validate_conformance.py && uv run scripts/validate_openapi.py'
run_shell_fails "mismatched-lock-failure" 'cd "'"$CLONE"'" && node -e '\''const fs = require("node:fs"); const pkg = JSON.parse(fs.readFileSync("package.json", "utf8")); pkg.dependencies.zod = "4.4.2"; fs.writeFileSync("package.json", JSON.stringify(pkg, null, 2) + "\n");'\'' && npm ci'

STATUS=completed
[[ ${#FAILURES[@]} -gt 0 ]] && STATUS=failed

{
  printf '{\n'
  printf '  "todo_id": 2,\n'
  printf '  "status": "%s",\n' "$STATUS"
  printf '  "qa_scenarios": [\n'
  printf '    "clean lock install",\n'
  printf '    "mismatched lock failure",\n'
  printf '    "README assertion",\n'
  printf '    "strict TypeScript typecheck",\n'
  printf '    "Node test runner against types/mbras.ts",\n'
  printf '    "PEP 723 validators through uv run",\n'
  printf '    "pinned project tool versions"\n'
  printf '  ],\n'
  printf '  "failures": ['
  for index in "${!FAILURES[@]}"; do
    [[ "$index" == "0" ]] || printf ', '
    printf '"%s"' "${FAILURES[$index]}"
  done
  printf ']\n'
  printf '}\n'
} > "$QA_SUMMARY"

uv run python scripts/qa/manifest.py "$REPORT" "$STATUS" 2 \
  .python-version \
  .npmrc \
  pyproject.toml \
  uv.lock \
  package.json \
  package-lock.json \
  tsconfig.json \
  types/mbras.ts \
  tests/types/mbras.test.ts \
  scripts/export_types_manifest.ts \
  scripts/validate_conformance.py \
  scripts/validate_openapi.py \
  scripts/qa/task-2.sh \
  README.md \
  "$COMMANDS_LOG" \
  "$QA_SUMMARY" \
  "$TYPE_MANIFEST"

[[ "$STATUS" == "completed" ]] || exit 1
