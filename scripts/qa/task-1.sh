#!/usr/bin/env bash
# QA for Todo 1: Bootstrap Git without committing local agent state.
# Usage: scripts/qa/task-1.sh --report .omo/evidence/task-1-manifest.json
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

PLAN_TRACKED="docs/plans/pibras-10-of-10-public-standard.md"
LOCK="governance/plan-lock.json"
FAILURES=()
check() { # check <name> <condition-exit-status>
  local name="$1" rc="$2"
  if [[ "$rc" -eq 0 ]]; then echo "PASS  $name"; else echo "FAIL  $name"; FAILURES+=("$name"); fi
}

sha() { shasum -a 256 "$1" | awk '{print $1}'; }

# 1. Git truth: repo on main, baseline tag, release branch
git rev-parse --is-inside-work-tree >/dev/null 2>&1; check "git-repo" $?
[[ "$(git branch --show-current)" == "main" ]]; check "branch-main" $?
git rev-parse -q --verify refs/tags/pibras-baseline >/dev/null; check "baseline-tag" $?
git rev-parse -q --verify refs/heads/release/pibras-v1 >/dev/null; check "release-branch" $?

# 2. Status clean
[[ -z "$(git status --porcelain)" ]]; check "status-clean" $?

# 3. Immutable plan identical to lock
LOCK_SHA="$(python3 -c "import json;print(json.load(open('$LOCK'))['sha256'])")"
[[ "$(sha "$PLAN_TRACKED")" == "$LOCK_SHA" ]]; check "plan-hash-matches-lock" $?

# 4. Forbidden paths untracked
FORBIDDEN_OK=0
for p in .omo .codegraph .ruff_cache .artifacts .env; do
  if git ls-files --error-unmatch "$p" >/dev/null 2>&1; then FORBIDDEN_OK=1; echo "  tracked forbidden path: $p"; fi
done
check "forbidden-paths-untracked" $FORBIDDEN_OK

# 5. Release path trackable (dist/release not ignored)
RP=0
git check-ignore -q dist/release/probe.txt && RP=1 || true
check "release-path-trackable" $RP

# 6. Clone + sentinel + cleanup: fresh clone must not contain local state,
#    and must contain the plan with the locked hash.
TMP="$(mktemp -d)"
SENTINEL="$TMP/sentinel"
git clone -q "$ROOT" "$SENTINEL"
CLONE_OK=0
[[ -f "$SENTINEL/$PLAN_TRACKED" ]] || CLONE_OK=1
[[ "$(sha "$SENTINEL/$PLAN_TRACKED")" == "$LOCK_SHA" ]] || CLONE_OK=1
for p in .omo .codegraph .ruff_cache .artifacts; do
  [[ -e "$SENTINEL/$p" ]] && { CLONE_OK=1; echo "  leaked into clone: $p"; }
done
check "clone-sentinel-clean" $CLONE_OK
rm -rf "$TMP"
[[ ! -d "$TMP" ]]; check "sentinel-cleanup" $?

# Manifest (standalone script: no heredoc/stdin dependency)
STATUS=completed; [[ ${#FAILURES[@]} -gt 0 ]] && STATUS=failed
python3 scripts/qa/manifest.py "$REPORT" "$STATUS" 1 \
  .gitignore \
  docs/plans/pibras-10-of-10-public-standard.md \
  governance/plan-lock.json \
  docs/REPOSITORY.md \
  scripts/qa/task-1.sh

[[ "$STATUS" == "completed" ]] || exit 1
