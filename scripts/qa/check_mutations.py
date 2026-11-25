"""Test-strength gate. Mutate one runtime rule at a time, never the test oracle."""
from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Mutation:
    rule: str
    source: str
    original: str
    replacement: str
    suite: str
    test: str


REGRESSIONS = "policy-and-mapper-regressions"
MUTATIONS = (
    Mutation("money", "types/mbras.ts", "amount: z.number().int()", "amount: z.number()",
             "mbras", "Money rejects fractional centavos"),
    Mutation("identity", "src/dedupe/matcher.ts", r'incoming.matricula.replace(/\D/g, "")', "incoming.matricula",
             "engine", "UnitMatcher accurately deduplicates properties by matricula and address"),
    Mutation("ownership", "types/mbras.ts", "  party_id: uuid,", "  party_id: uuid.optional(),",
             "ownership-link", "Ownership requires a party link"),
    Mutation("policy", "src/policy/evaluator.ts",
             'evalResult.decision !== "allow" && evalResult.decision !== "mask"',
             'evalResult.decision === "deny"', REGRESSIONS,
             "projectForChannel blocks needs_approval as unpublishable"),
    Mutation("projection", "src/policy/evaluator.ts", "if (keep.has(key))",
             'if (keep.has(key) || key === "matricula")',
             REGRESSIONS, "projectForChannel honours the allow rule field allowlist"),
)


def run(root, case):
    args = ["node", "--experimental-strip-types", "--test", "--test-reporter=tap",
            f"--test-name-pattern=^{re.escape(case.test)}$", f"tests/types/{case.suite}.test.ts"]
    return subprocess.run(args, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, timeout=90)


def outcome(root, case):
    path = root / case.source
    source = path.read_text(encoding="utf-8")
    if source.count(case.original) != 1:
        return "ERROR", f"expected unique mutation site in {case.source}"
    baseline = run(root, case)
    label = rf"\d+ - {re.escape(case.test)}$"
    if baseline.returncode or not re.search("^ok " + label, baseline.stdout, re.M):
        return "ERROR", "control did not pass:\n" + baseline.stdout
    path.write_text(source.replace(case.original, case.replacement), encoding="utf-8")
    mutated = run(root, case)
    if not mutated.returncode:
        return "SURVIVED", "gate remained green"
    if (mutated.returncode == 1 and re.search("^not ok " + label, mutated.stdout, re.M)
            and "ERR_ASSERTION" in mutated.stdout):
        return "KILLED", case.test
    return "ERROR", "unexpected failure (not a kill):\n" + mutated.stdout


def main():
    failed = False
    for case in MUTATIONS:
        try:
            with tempfile.TemporaryDirectory(prefix="pibras-mutant-") as tmp:
                root = Path(tmp)
                for name in ("src", "types", "tests", "mappings"):
                    shutil.copytree(ROOT / name, root / name)
                shutil.copy2(ROOT / "package.json", root)
                (root / "node_modules").symlink_to(ROOT / "node_modules", target_is_directory=True)
                status, detail = outcome(root, case)
        except (OSError, subprocess.TimeoutExpired) as exc:
            status, detail = "ERROR", str(exc)
        print(f"{case.rule}: {status}: {detail}", flush=True)
        failed |= status != "KILLED"
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
