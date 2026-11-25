#!/usr/bin/env bash
# Canonical local and GitHub Actions verification, including frozen bootstrap.
set -euo pipefail
cd "$(dirname "$0")/../.."
case "${1:-}" in
  conformance|contracts) mode=$1 ;;
  *) echo 'Usage: scripts/qa/verify.sh {conformance|contracts}' >&2; exit 2 ;;
esac
printf 'Verifying %s at %s\n' "$mode" "$(git rev-parse HEAD)"
if [[ -n "${GITHUB_RUN_ID:-}" ]]; then
  printf 'CI run: %s/%s/actions/runs/%s\n' "$GITHUB_SERVER_URL" "$GITHUB_REPOSITORY" "$GITHUB_RUN_ID"
fi
set -x
[[ "$(uv --version | cut -d' ' -f2)" == 0.9.7 ]]
uv lock --check
# Explicit "python" runs each file with uv.lock, not isolated PEP 723 resolution.
py=(uv run --no-sync python)
if [[ "$mode" == conformance ]]; then
  uv sync --frozen --no-default-groups
  "${py[@]}" scripts/validate_conformance.py
  exit
fi
uv sync --frozen
[[ "$(node -p 'process.versions.node')" == "$(node -p "require('./package.json').engines.node")" ]]
[[ "$(npm --version)" == "$(node -p "require('./package.json').engines.npm")" ]]
npm ci
uv run --no-sync pip-audit --local --strict
npm audit --audit-level=moderate
git ls-files -z | xargs -0 uv run --no-sync detect-secrets-hook --baseline .secrets.baseline
uv run --no-sync pytest
npm run typecheck
npm run test:types
"${py[@]}" scripts/validate_conformance.py
"${py[@]}" scripts/validate_openapi.py
uv run --no-sync openapi-spec-validator openapi.yaml
"${py[@]}" scripts/check_contract_parity.py
"${py[@]}" scripts/check_semantic_parity.py
"${py[@]}" scripts/check_domain_invariants.py --entities tests/contracts/aligned/entities
"${py[@]}" scripts/check_identity.py
"${py[@]}" scripts/validate_release_policy.py governance/release-policy.yaml
bash tests/postgres/run.sh
"${py[@]}" scripts/qa/check_mutations.py
