#!/usr/bin/env bash
# QA for Todo 5: reconcile v0.1.0 artifacts into a coherent v0.2 release candidate.
# Usage: scripts/qa/task-5.sh --report .omo/evidence/task-5-manifest.json
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
COMMANDS_LOG="$EVIDENCE_DIR/task-5-commands.log"
QA_SUMMARY="$EVIDENCE_DIR/task-5-qa-summary.json"
: > "$COMMANDS_LOG"

record_failure() {
  local name="$1"
  FAILURES+=("$name")
  echo "FAIL  $name"
}

run_ok() {
  local name="$1"
  shift
  local log="$EVIDENCE_DIR/task-5-$name.log"
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

# Real repo contract surfaces must be fully reconciled: parity green.
run_ok "parity-real-green" uv run scripts/check_contract_parity.py --root .

# Domain invariants stay green on aligned fixtures.
run_ok "invariants-aligned-green" uv run scripts/check_domain_invariants.py --entities tests/contracts/aligned/entities

# Full contract gate suite (aligned green, frozen red, real green).
run_ok "pytest-gates" uv run pytest tests/contracts/ -q

# Cross-surface validators.
run_ok "validate-conformance" uv run scripts/validate_conformance.py
run_ok "validate-openapi" uv run scripts/validate_openapi.py

# TypeScript/Zod surface.
run_shell_ok "typecheck" "npm run --silent typecheck"
run_shell_ok "test-types" "npm run --silent test:types"

# Migration doc must exist and cover the reconciled surfaces.
run_shell_ok "migration-doc-present" "test -s docs/migrations/v0.1.0-to-v0.2.md"
run_shell_ok "migration-doc-covers-audit-enum" "grep -q audit_change_type docs/migrations/v0.1.0-to-v0.2.md"

# Todo 4 harness remains green end-to-end.
run_ok "task-4-harness-green" bash scripts/qa/task-4.sh --report "$EVIDENCE_DIR/task-4-manifest.json"

run_ok "shellcheck-task-5" uv run shellcheck scripts/qa/task-5.sh

STATUS=completed
[[ ${#FAILURES[@]} -gt 0 ]] && STATUS=failed

{
  printf '{\n'
  printf '  "todo_id": 5,\n'
  printf '  "status": "%s",\n' "$STATUS"
  printf '  "qa_scenarios": [\n'
  printf '    "real repo contract parity green (zero findings)",\n'
  printf '    "domain invariants green",\n'
  printf '    "contract gate suite passes (aligned green, frozen red, real green)",\n'
  printf '    "conformance and OpenAPI validators pass",\n'
  printf '    "TypeScript typecheck and type tests pass",\n'
  printf '    "migration doc v0.1.0-to-v0.2 present and covers DDL enum change",\n'
  printf '    "Todo 4 harness still completes"\n'
  printf '  ],\n'
  printf '  "failures": ['
  for index in "${!FAILURES[@]}"; do
    [[ "$index" == "0" ]] || printf ', '
    printf '"%s"' "${FAILURES[$index]}"
  done
  printf ']\n'
  printf '}\n'
} > "$QA_SUMMARY"

uv run python scripts/qa/manifest.py "$REPORT" "$STATUS" 5 \
  docs/migrations/v0.1.0-to-v0.2.md \
  mappings/v0.1.0-code-to-v0.2.md \
  db/schema.sql \
  schema/mbras.schema.json \
  types/mbras.ts \
  tests/contracts/test_gates.py \
  tests/contracts/aligned/contracts/types/mbras.ts \
  tests/contracts/pre-reconciliation/contracts/types/mbras.ts \
  scripts/qa/task-4.sh \
  scripts/qa/task-5.sh \
  "$COMMANDS_LOG" \
  "$QA_SUMMARY"

[[ "$STATUS" == "completed" ]] || exit 1
