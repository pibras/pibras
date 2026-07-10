#!/usr/bin/env bash
# Task 3 QA: identity scanner + release-policy validation (happy, missing-approval, URL-mutation)
set -uo pipefail
cd "$(git rev-parse --show-toplevel)"
RUN="uv run --with pyyaml --with jsonschema python"
mkdir -p .omo/evidence
declare -a NAMES RESULTS

record() { NAMES+=("$1"); RESULTS+=("$2"); echo "[$2] $1"; }

# 1. happy path: scanner passes
$RUN scripts/check_identity.py && record identity-scan-clean PASS || record identity-scan-clean FAIL
# 2. happy path: policy validates
$RUN scripts/validate_release_policy.py && record policy-valid PASS || record policy-valid FAIL
# 3. negative: remove identity approval -> must fail
python3 - <<'PY'
import pathlib
t = pathlib.Path("governance/release-policy.yaml").read_text()
pathlib.Path("/tmp/rp.bak").write_text(t)
pathlib.Path("governance/release-policy.yaml").write_text(t.split("approvals:")[0] + "approvals: []\n")
PY
$RUN scripts/validate_release_policy.py 2>/dev/null && record missing-approval-rejected FAIL || record missing-approval-rejected PASS
cp /tmp/rp.bak governance/release-policy.yaml
# 4. negative: mutate canonical repo URL -> must fail
python3 - <<'PY'
import pathlib
t = pathlib.Path("governance/release-policy.yaml").read_text()
pathlib.Path("governance/release-policy.yaml").write_text(t.replace("github.com/ibvi-br/pibras.git", "github.com/other-org/pibras.git"))
PY
$RUN scripts/validate_release_policy.py 2>/dev/null && record url-mutation-rejected FAIL || record url-mutation-rejected PASS
cp /tmp/rp.bak governance/release-policy.yaml
# 5. negative: branded token in tracked file -> scanner must fail
echo "MBRAS leak test" > /tmp/qa_leak.md && cp /tmp/qa_leak.md qa_leak_probe.md && git add qa_leak_probe.md
$RUN scripts/check_identity.py 2>/dev/null && record brand-leak-rejected FAIL || record brand-leak-rejected PASS
git rm -q --cached qa_leak_probe.md && rm -f qa_leak_probe.md

FAILS=0
{ echo '{'
  echo '  "task": "task-3", "checks": ['
  for i in "${!NAMES[@]}"; do
    [ "${RESULTS[$i]}" = "FAIL" ] && FAILS=$((FAILS+1))
    sep=","; [ "$i" = "$((${#NAMES[@]}-1))" ] && sep=""
    echo "    {\"name\": \"${NAMES[$i]}\", \"status\": \"${RESULTS[$i]}\"}$sep"
  done
  echo "  ], \"failures\": $FAILS, \"recorded_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\""
  echo '}'
} > .omo/evidence/task-3-manifest.json
cat .omo/evidence/task-3-manifest.json
exit $FAILS
