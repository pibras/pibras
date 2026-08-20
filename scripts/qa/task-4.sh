#!/usr/bin/env bash
# QA for Todo 4: Build red-first parity and domain-invariant harnesses.
# Usage: scripts/qa/task-4.sh --report .omo/evidence/task-4-manifest.json
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
COMMANDS_LOG="$EVIDENCE_DIR/task-4-commands.log"
QA_SUMMARY="$EVIDENCE_DIR/task-4-qa-summary.json"
: > "$COMMANDS_LOG"

record_failure() {
  local name="$1"
  FAILURES+=("$name")
  echo "FAIL  $name"
}

run_ok() {
  local name="$1"
  shift
  local log="$EVIDENCE_DIR/task-4-$name.log"
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
  local log="$EVIDENCE_DIR/task-4-$name.log"
  printf '$ bash -lc %q\n' "$command" > "$log"
  printf '%s\t%s\n' "$name" "$command" >> "$COMMANDS_LOG"
  if bash -lc "$command" >> "$log" 2>&1; then
    record_failure "$name"
  else
    echo "PASS  $name"
  fi
}

# Aligned fixtures: direct checks must be green (exit 0).
run_ok "parity-aligned-green" uv run scripts/check_contract_parity.py --root tests/contracts/aligned/contracts
run_ok "invariants-aligned-green" uv run scripts/check_domain_invariants.py --entities tests/contracts/aligned/entities

# Frozen pre-reconciliation fixtures: direct checks must be red (exit non-zero).
run_shell_fails "parity-frozen-expected-red" "uv run scripts/check_contract_parity.py --root tests/contracts/pre-reconciliation/contracts"
run_shell_fails "invariants-frozen-expected-red" "uv run scripts/check_domain_invariants.py --entities tests/contracts/pre-reconciliation/entities"

# Direct target checks against the REAL repo contracts: green as of the
# v0.2 reconciliation (Todo 5); they were expected red before it.
run_ok "parity-real-green" uv run scripts/check_contract_parity.py --root .

# Harness: pytest must exit 0 even though targets are red (red-first).
run_ok "pytest-gates" uv run pytest tests/contracts/test_gates.py -q

# Regressions: existing validators stay green.
run_ok "validate-conformance" uv run scripts/validate_conformance.py
run_ok "validate-openapi" uv run scripts/validate_openapi.py
run_ok "shellcheck-task-4" uv run shellcheck scripts/qa/task-4.sh

STATUS=completed
[[ ${#FAILURES[@]} -gt 0 ]] && STATUS=failed

{
  printf '{\n'
  printf '  "todo_id": 4,\n'
  printf '  "status": "%s",\n' "$STATUS"
  printf '  "qa_scenarios": [\n'
  printf '    "aligned synthetic fixtures green",\n'
  printf '    "frozen pre-reconciliation fixtures expected red",\n'
  printf '    "real repo contracts green after Todo 5 reconciliation",\n'
  printf '    "pytest harness exits 0 with exact expected finding IDs",\n'
  printf '    "identity rules excluded from blocking and manifest",\n'
  printf '    "existing validators unaffected"\n'
  printf '  ],\n'
  printf '  "failures": ['
  for index in "${!FAILURES[@]}"; do
    [[ "$index" == "0" ]] || printf ', '
    printf '"%s"' "${FAILURES[$index]}"
  done
  printf ']\n'
  printf '}\n'
} > "$QA_SUMMARY"

uv run python scripts/qa/manifest.py "$REPORT" "$STATUS" 4 \
  scripts/check_contract_parity.py \
  scripts/check_domain_invariants.py \
  scripts/validate_conformance.py \
  scripts/export_schema_org.py \
  mappings/schema-org-to-pibras.md \
  tests/golden/conformance-cases.json \
  tests/golden/schema-org.property-public.json \
  tests/golden/schema-org.leaked-restricted-fields.invalid.json \
  tests/golden/schema-org.status-draft.invalid.json \
  tests/golden/schema-org.status-off-market.invalid.json \
  tests/golden/schema-org.status-archived.invalid.json \
  tests/contracts/expected-red-manifest.json \
  tests/contracts/test_gates.py \
  tests/contracts/pre-reconciliation/README.md \
  tests/contracts/pre-reconciliation/contracts/schema/mbras.schema.json \
  tests/contracts/pre-reconciliation/contracts/types/mbras.ts \
  tests/contracts/pre-reconciliation/contracts/db/schema.sql \
  tests/contracts/pre-reconciliation/entities/buildings.json \
  tests/contracts/pre-reconciliation/entities/units.json \
  tests/contracts/pre-reconciliation/entities/properties.json \
  tests/contracts/aligned/README.md \
  tests/contracts/aligned/contracts/schema/mbras.schema.json \
  tests/contracts/aligned/contracts/types/mbras.ts \
  tests/contracts/aligned/contracts/db/schema.sql \
  tests/contracts/aligned/entities/buildings.json \
  tests/contracts/aligned/entities/units.json \
  tests/contracts/aligned/entities/properties.json \
  scripts/qa/task-4.sh \
  "$COMMANDS_LOG" \
  "$QA_SUMMARY"

[[ "$STATUS" == "completed" ]] || exit 1
