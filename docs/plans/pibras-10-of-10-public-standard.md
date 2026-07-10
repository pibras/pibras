# pibras-10-of-10-public-standard - Work Plan

## TL;DR (For humans)
<!-- Fill this LAST, after the detailed plan below is written, so it summarizes the REAL plan. -->
<!-- Plain English for a non-engineer: NO file paths, NO todo numbers, NO wave/agent/tool names. -->

**What you'll get:** A neutral, versioned, reproducible PIBRAS public standard whose domain contracts, database model, API definition, privacy rules, governance, licenses, and release artifacts are all executable and independently verifiable. The result culminates in a signed v1.0.0 release bundle rather than a documentation-only claim.

**Why this approach:** Repository and public identity foundations come first so later parity tests do not freeze temporary MBRAS-branded assumptions. Tests are added before reconciliation, and the exact same aggregate gate runs locally, in CI, and against the packaged release.

**What it will NOT do:** It will not build a CRM, UI, hosted API, ingestion platform, or production database. It will not silently treat experimental roadmap entities as stable, and it will not publish until neutral identity, legal licensing, maintainer RFC, and signing approvals are real.

**Effort:** XL
**Risk:** High - contract reconciliation spans four executable representations and the final release depends on legal, institutional, and cryptographic approvals outside code.
**Decisions to sanity-check:** v0.2 acceptance precedes v1.0 maturity; public identity must be neutral before parity snapshots; Apache-2.0 covers technical artifacts and CC BY 4.0 covers documentation subject to legal approval; experimental commercial/intelligence entities remain outside v1 conformance.

Your next move: choose whether to start execution or run the optional dual high-accuracy plan review first. Full execution detail follows below.

---

> TL;DR (machine): XL/high-risk 12-todo roadmap delivering Git bootstrap, neutral identity, locked toolchains, parity/invariant gates, v0.2 reconciliation, secured OpenAPI, PostgreSQL validation, mutation coverage, CI, governance/licensing, and a signed v1.0.0 bundle.

## Scope
### Must have
- A Git repository before any CI, PR, tag, release, or branch-protection work.
- One approved neutral organization/domain used consistently by the remote, JSON Schema `$id`, OpenAPI servers, documentation, and release metadata before parity snapshots are finalized.
- Reproducible Python 3.13 + uv and Node 22 + npm toolchains with committed `uv.lock` and `package-lock.json`.
- Executable authority/parity checks across accepted RFC, normative docs, JSON Schema, OpenAPI, Zod, DDL, mappings, examples, and golden fixtures.
- Explicit v0.1.0 to v0.2 reconciliation, compatibility evidence, and migration report.
- Real PostgreSQL 16 DDL application locally and in CI through the same Docker-backed script.
- Conformance and mutation coverage for structure, formats, policy, projection, API security, DDL, migration, and release metadata.
- `scripts/check_all.sh` as the only aggregate local/CI validation entry point.
- Accepted RFC, complete governance/LGPD/security/contribution/changelog artifacts, legally approved dual licensing, release candidate evidence, and a signed v1.0.0 release only after F1-F4 approval and explicit final-user confirmation.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- No hosted production API, CRM, UI, ingestion service, cloud database, business-data migration, SDK family, or deployment platform.
- Do not delete experimental commercial/intelligence tables merely because they remain outside v1 conformance.
- Do not publish, tag v1.0.0, add public license claims, or configure an MBRAS-branded public schema root before the corresponding external approval gates pass.
- Do not use bare `python3 scripts/validate_*.py`; PEP 723 validators run through `uv run`.
- Do not duplicate CI logic in YAML; CI invokes `scripts/check_all.sh`.
- Do not weaken validators or fixtures to make parity pass.

## Verification strategy
> All technical verification is agent-executed; external approvals are recorded inputs and remain non-automatable blockers.
- This statement applies only to technical verification. Neutral-identity approval, maintainer RFC acceptance, legal licensing approval, and release-signing authorization are external approval gates; automation verifies their recorded evidence but cannot manufacture or replace them.
- Test decision: TDD. Python checks use `pytest` plus CLI subprocess assertions; TypeScript uses Node's test runner against Zod; SQL uses `psql` assertions in PostgreSQL 16; shell uses `shellcheck`; mutation tests operate only in disposable copies.
- Canonical happy-path requires exact runtimes, Docker/image digest, required network, and phase-appropriate approvals; then `scripts/check_all.sh --mode ci --report .artifacts/check-all.json` exits 0 from a clean checkout. Bare no-argument invocation is unsupported and exits with usage error 64.
- Environment prerequisites: Docker Engine with Linux containers and outbound HTTPS access to the npm registry, Python package/audit indexes, GitHub API/actions, Apache, and Creative Commons. Required-network failure exits 2 with a named `NETWORK_REQUIRED:<service>` status; release work does not substitute stale or unverified data.
- Exact runtime pins are Python `3.13.9`, uv `0.9.7`, Node `22.22.3`, npm `10.9.8`, and `docker.io/library/postgres:16-alpine@sha256:57c72fd2a128e416c7fcc499958864df5301e940bca0a56f58fddf30ffc07777`; local/CI preflight rejects mismatches. Docker pulls require `registry-1.docker.io` network or a preloaded image with the identical digest.
- PyPI dev-tool pins are `shellcheck-py==0.11.0.1`, `pip-audit==2.10.1`, `detect-secrets==1.5.0`, and `openapi-spec-validator==0.9.0`, locked by `uv.lock`; canonical preflights are `uv run shellcheck --version`, `uv run pip-audit --version`, `uv run detect-secrets --version`, and `uv run openapi-spec-validator --version`.
- All runtime and package pins are approved immutable inputs, not executor choices. If any exact pin is unavailable, execution terminates BLOCKED with registry evidence; there is deliberately no automatic fallback. Resuming requires an owner-approved plan amendment and a new high-accuracy review.
- Pin availability was independently resolved during planning on 2026-07-09: `npm view typescript@7.0.2 version` returned `7.0.2`, `npm view zod@4.4.3 version` returned `4.4.3`, and PyPI JSON for `openapi-spec-validator/0.9.0` returned `0.9.0`. Todo 2 repeats these as drift/network preflights, not unresolved version decisions.
- Canonical failure proof: each gate has a targeted mutation or malformed fixture that makes the corresponding command exit non-zero without modifying the worktree.
- Todo completion state is exclusively `.omo/evidence/task-<N>-manifest.json`; logs/reports are artifacts referenced by it. Each artifact entry has `path`, `sha256`, and `bundle`. The RC bundle copies completed Todo 1-11 manifests and their `bundle: true` artifacts; Todo 12's manifest and its pretag/posttag reports remain external because they complete only around tag creation. F1-F4 verifier verdict files are a separate final-approval evidence class and never substitute for, or alter, Todo completion state.

### Execution invariants
- The tracked plan is immutable approved input: no Todo or F1-F5 checkbox is edited. `scripts/check_plan_evidence.py` derives state only from evidence manifests.
- If execution discovers that this plan itself needs correction after Todo 1, work stops BLOCKED; the owner must approve a new versioned plan path and lock hash, and dual high-accuracy review restarts. Executors never silently mutate the locked plan, so immutability is intentional rather than a missing repair path.
- Todo 1 copies this approved plan byte-for-byte to tracked `docs/plans/pibras-10-of-10-public-standard.md` and records its SHA-256 in tracked `governance/plan-lock.json`; `scripts/check_plan_evidence.py` accepts only that path and requires its current hash to equal the lock before reading evidence.
- `pyproject.toml` dependency groups and `uv.lock` are Python authority; PEP 723 exists only on the two standalone validators and mirrors their runtime subset. OpenAPI/ShellCheck/audit commands use the project environment, not PEP 723.
- Todo 3 configures origin, requires `git ls-remote --heads --tags origin` exit 0, and checks exact approved URL/ref state.
- Release-policy phases are schema-defined: `identity` requires identity fields; `rfc_accepted` additionally requires two maintainer approvals; `legal_approved` adds legal approver/source URLs/retrieval timestamps/approved SHA-256 hashes; `rc` adds signing fingerprint/public-key path/candidate artifact version; `final` adds final-promotion approval and final artifact version. Phase checkers reject missing earlier-phase fields. CI autodetects and validates the highest phase represented by policy: Todo 9 `identity`, Todo 10 `rfc_accepted`, Todo 11 `legal_approved`, Todo 12 and F2 `rc`, and F5 `final`. Release-pretag/posttag explicitly require `rc` or `final` according to the tag.
- Aggregate modes are explicit: `--mode ci --report <path>` never reads `.omo` as an input, although `<path>` may be an output below `.omo/evidence/`; `--mode release-pretag --bundle <path> --evidence <path> --tag <tag> --fingerprint <fp> --report <path>` validates bundle DAG/approvals but not tag existence; `--mode release-posttag` takes the same arguments plus `--external-evidence <path>` and adds tag/fingerprint/posttag verification. `check_release.py` is internal except independent F1/F5 audit.
- OpenAPI parity in Todo 5 is structural for entities/fields only; Todo 6 adds security, required external refs, and endpoint completeness, after which Todo 9 enforces final OpenAPI parity.
- RC immutability: `governance/final-promotion-approval.yaml` is created only in the F5 commit on top of the reviewed RC commit. It is an explicitly allowed final-only metadata difference.
- Release source identity is non-self-referential: `scripts/hash_release_sources.py` hashes sorted Git tree records (`<mode> <type> <object>\t<path>\n`) for `README.md`, `docs/` excluding `docs/plans/`, `schema/`, `types/`, `db/`, `examples/`, `mappings/`, `tests/golden/`, and `openapi.yaml`; it excludes `dist/`, evidence, and release-policy metadata. Bundle field `source_snapshot_sha` is this digest, and pre/post-merge checks recompute it from the exact commit.
- `scripts/compare_release.py` separately compares the complete recursively sorted RC/final bundle path set and bytes. It permits only paths and transformations declared in `governance/final-release-allowlist.yaml`, including final approval metadata and derived checksum/signature files; every unlisted added, removed, or changed byte fails. This full-bundle comparison is independent of `source_snapshot_sha`.
- Release hashing is a deterministic DAG: `artifact-manifest.json` lists/hashes payload files only and excludes itself plus reserved `CHECKSUMS.txt`/`CHECKSUMS.txt.asc`; sorted `CHECKSUMS.txt` hashes every payload plus `artifact-manifest.json`; detached `CHECKSUMS.txt.asc` signs only `CHECKSUMS.txt`. The checker validates reserved files by these rules and rejects every undeclared non-reserved file.
- Identity exemption marker is exactly `Status: historical and non-authoritative`; required once near the top of exempt historical docs. `docs/plans/**` is always excluded from identity scanning as immutable execution history. Compatibility fixture notes must contain exact token `[compatibility]`.
- Todo 4 writes frozen minimal fixtures under `tests/contracts/pre-reconciliation/` plus `expected-red.json`; aggregate tests use only that frozen set after Todo 5. The one-time root red run is evidence, and Todo 5 consumes every ID exactly once.
- DDL transaction precheck rejects `CREATE INDEX CONCURRENTLY`, `DROP INDEX CONCURRENTLY`, `VACUUM`, `REINDEX CONCURRENTLY`, and transaction-control statements other than the single outer `BEGIN`/`COMMIT`.
- Mutation manifest entries use JSON fields `id`, `category`, `target`, `unified_diff`, `command`, `cwd`, `timeout_seconds`, `expected_exit`, `expected_rule`, and `environment`; each runs alone with sanitized environment, bounded timeout, Docker/network disabled unless the owning category explicitly declares it, and guaranteed temp/container cleanup.
- Any required-network outage, including F2 GitHub verification, yields BLOCKED exit 2 and can never produce APPROVE.
- Exact CI pins are immutable plan inputs: `actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5`, `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`, `actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020`, `astral-sh/setup-uv@d0cc045d04ccac9d8b7881df0226f9e82c39688e`, and `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02`.
- Final commit ancestry is linear: F5 creates one new commit on top of the reviewed RC commit; it never amends or moves the RC tag.
- F1-F4 evidence filenames are exactly `final-f1-plan-compliance.md`, `final-f2-code-quality.md`, `final-f3-independent-qa.md`, and `final-f4-scope-fidelity.md`. Each begins with YAML fields `verdict`, `rc_tag`, `reviewer`, `started_at`, `finished_at`, `commands` (command/exit/output_hash), and `findings`; only `verdict: APPROVE` passes.
- Before cloning, the final-wave coordinator in the originating workspace sets `ORIGIN_EVIDENCE_DIR="$(pwd)/.omo/evidence"` and creates it. It launches each F2-F4 reviewer process/subagent with that absolute value embedded in the task invocation (`env ORIGIN_EVIDENCE_DIR="$ORIGIN_EVIDENCE_DIR" <review-command>` or an equivalent explicit task argument); reviewers must echo and validate the absolute writable directory before cloning. They write reports inside their clones first, then atomically copy the exact verdict file to `$ORIGIN_EVIDENCE_DIR/<required-filename>` and emit the copied file's SHA-256 to the coordinator; F5 hashes those origin files again before bundling. A missing/mismatched receipt is BLOCKED.
- Canonical approval files are `governance/release-policy.yaml` validated by `schema/release-policy.schema.json` for identity, maintainer, legal, signing, and RC phases, plus `governance/final-promotion-approval.yaml` for F5 only. F5 creates and validates the final file before any pretag command; when tag/version is `v1.0.0`/`1.0.0`, both pretag and posttag combine it with the RC policy and require the resulting `final` phase.
- The two PEP 723 scripts are exactly `scripts/validate_conformance.py` (`jsonschema[format]`) and `scripts/validate_openapi.py` (`PyYAML`); their direct path invocations use inline metadata. Project-only commands such as `uv run openapi-spec-validator` use `pyproject.toml`/`uv.lock`.
- Every Todo's only state file is `.omo/evidence/task-<N>-manifest.json` with `todo_id`, `status`, `started_at`, `finished_at`, `commands`, `qa_scenarios`, `artifacts`, and `commit`; every other cited log/report is supplementary and referenced from that manifest, regardless of older prose filenames. Each Todo runs `scripts/qa/task-<N>.sh --report` against this canonical file.
- RC values are parameterized from release policy: `RC_ARTIFACT_VERSION`, `RC_TAG=v${RC_ARTIFACT_VERSION}`, and `RC_BUNDLE=dist/pibras-${RC_ARTIFACT_VERSION}`. Literal `1.0.0-rc.1` denotes only the initial value; scripts/checkers never hardcode it, so failed attempts increment policy and automatically update F1-F4 paths/commands.
- Existing filenames `schema/mbras.schema.json` and `types/mbras.ts` are bounded v1 compatibility aliases, not public identity claims; contents/IDs are neutral, README labels them compatibility paths, identity tests allow only these two names, and removal cannot occur before v2.0 migration.
- Every independent final verifier uses a non-shallow clone, fetches tags, runs `git checkout --detach "$RC_TAG"`, and asserts `git rev-parse HEAD` equals `git rev-parse "$RC_TAG^{}"` before checks.

### External approval and signing input contract
- Before Todo 3 completion: scaffolding may begin without approval, but Todo 3 cannot commit, configure/push remote, or unblock Todo 5 until approved GitHub/identity inputs exist.
- Todo 3's first gated action is to receive those owner-produced inputs as a signed-off record, validate them against `schema/release-policy.schema.json`, and copy them into `governance/release-policy.yaml`; input acquisition is an explicit external owner gate, not an agent-generated step. Until supplied, Todo 3 remains BLOCKED before commit or remote configuration.
- Those inputs are `hosting.provider: github`, repository owner/name/URL, neutral organization, schema root, docs URL, approver/date/evidence; repository URL is `https://github.com/<owner>/<name>.git`, while schema/docs hosts are independently approved.
- Before Todo 10 can change the RFC state to Accepted: record at least two named maintainers, their approval dates, and immutable review references. Missing approval leaves the RFC in Review and blocks Todo 12.
- Before Todo 11: record legal approver/date/licenses/evidence plus both canonical source URLs, retrieval timestamps, and the exact approved SHA-256 hashes stated in Todo 11. Missing approval preserves the stub and blocks Todo 12.
- Before Todo 12: record the OpenPGP signing fingerprint and authorized signer identity. Preflight requires `gpg --list-secret-keys <fingerprint>` and `git config gpg.format openpgp`; tag creation uses `git tag -s`, and verification uses `git verify-tag`. Missing signing material blocks release without weakening the gate.
- Before F5: an explicit user instruction such as “promote v1.0.0” may be recorded, never inferred, in tracked `governance/final-promotion-approval.yaml` with `requested_by`, `approved_at`, `source_type: codex_task`, and non-secret task/thread reference. It gates only F5, not RC verification.
- External approvals are never inferred from conversation text, generated by an agent, or represented by placeholder values.

## Execution strategy
### Parallel execution waves
> This roadmap is dependency-driven; singleton bootstrap and sequential release waves are intentional.
- Wave 0: Todo 1 only as an explicit exception to the 5-8 target, because no later work can start before Git truth exists.
- Wave 1: Todo 2 first; then Todos 3 and 4 may run in parallel. Identity approval blocks Todo 3 completion and Todo 5 reconciliation snapshots, not Todo 4's explicitly historical pre-reconciliation fixtures or synthetic harness scaffolding.
- Wave 2: Todos 5-8 after authority, toolchain, and red parity gates exist.
- Wave 3 is sequential: Todo 9 aggregate CI, Todo 10 governance, Todo 11 approved licensing/release checks, then Todo 12 RC construction.
- Final wave: F1-F4 in parallel after all todos and external gates are satisfied.

### Dependency matrix
| Todo | Depends on | Blocks | Can parallelize with |
| --- | --- | --- | --- |
| 1 | - | 2-12 | - |
| 2 | 1 | 3-12 | - |
| 3 | 1,2 | 5,6,10,11,12 | 4 |
| 4 | 1,2 | 5-9 | 3 |
| 5 | 2,3,4 | 6-12 | - |
| 6 | 5 | 8-12 | 7 |
| 7 | 2,4,5 | 8,9,10,12 | 6 |
| 8 | 5,6,7 | 9,10,12 | - |
| 9 | 6,7,8 | 10,12 | - |
| 10 | 6-9; maintainer RFC acceptance is its completion gate | 11,12 | - |
| 11 | 3,5,10 plus legal approval and accepted RFC | 12 | - |
| 12 | 9-11 plus signing authorization and available secret key | F1-F4 | - |

## Todos
> Implementation + Test = ONE todo. Never separate.
> For every Todo N, the prose QA cases are implemented and executed by mandatory `scripts/qa/task-N.sh --report .omo/evidence/task-N-manifest.json`; the manifest is the only completion state.
<!-- APPEND TASK BATCHES BELOW THIS LINE WITH edit/apply_patch - never rewrite the headers above. -->
- [ ] 1. Bootstrap Git without committing local agent state
  What to do / Must NOT do: Create `.gitignore` for `.omo/`, `.artifacts/`, caches, secrets, local state, and dist with release exceptions. Copy the approved plan byte-for-byte to `docs/plans/pibras-10-of-10-public-standard.md`, write its SHA-256 to `governance/plan-lock.json`, and never edit that tracked copy. Create `docs/REPOSITORY.md` defining local bootstrap, baseline tag, branch topology, deferred neutral remote, protected-main transition, rebase-only merges, and RC/final tag policy; initialize `main`, create annotated baseline tag, and create local-only branch `release/pibras-v1`; defer configuring/pushing the remote until Todo 3. Create the canonical task-1 QA script and evidence-manifest writer, but do not create the release artifact manifest/checker that belongs to Todo 11.
  Parallelization: Wave 0 | Blocked by: none | Blocks: 2-12
  References (executor has NO interview context - be exhaustive): `AGENTS.md`; current workspace root has no `.git`; `.codegraph` is a local symlink; `GOVERNANCE.md:14-17` requires neutral public identity.
  Acceptance criteria (agent-executable): after sentinel cleanup, Git/main/baseline/tag are correct, status clean, immutable plan identical, forbidden paths untracked, and release path trackable. Every evidence manifest records `todo_id` and `status: completed`; downstream readers treat those manifests, never unchecked Markdown boxes, as execution state.
  QA scenarios: mandatory task-1 QA script covers clone/sentinel/cleanup and writes `.omo/evidence/task-1-manifest.json`.
  Commit: Y | `chore(repo): establish PIBRAS baseline`

- [ ] 2. Lock Python and TypeScript toolchains and canonical commands
  What to do / Must NOT do: Pin the exact Python versions listed. PEP 723 mirrors runtime only. In `package.json`, set exact JSON values `"typescript": "7.0.2"` and `"zod": "4.4.3"` with `save-exact=true` and lockfile v3. Add strict config/tests/manifest exporter. Sequence: manifests, locks, commit, frozen clean-clone acceptance.
  Parallelization: Wave 1 | Blocked by: 1 | Blocks: 3-12
  References: `README.md:70-75`; `types/mbras.ts:8-13`; `scripts/validate_conformance.py:1-8`; `scripts/validate_openapi.py:1-8`.
  Acceptance criteria: preflight `npm view typescript@7.0.2 version`, `npm view zod@4.4.3 version`, and `uv lock --check`/fresh lock resolution prove all exact versions available; unavailable registry/version exits 2 BLOCKED. Frozen checks then pass; ShellCheck/OpenAPI versions and npm tests match pins.
  QA scenarios: mandatory task-2 QA script covers clean lock install, mismatched lock failure, and README assertion; writes `.omo/evidence/task-2-manifest.json`.
  Commit: Y | `build(toolchain): lock Python and TypeScript checks`

- [ ] 3. Resolve neutral identity and contract authority before snapshots
  What to do / Must NOT do: Create release-policy/schema/checker. Todo 1's `release/pibras-v1` is local-only; before this Todo configures origin, no remote ref is assumed. Use `git ls-remote --heads --tags origin` so symbolic HEAD is excluded; this command does emit the annotated tag's `^{}` peeled line. Pre-push allowed refs are empty or matching main+baseline; push main, the baseline tag, and `release/pibras-v1`; post-push allowed refs are exactly those three direct refs plus the baseline tag's peeled `refs/tags/pibras-baseline^{}` line. Extra/mismatch BLOCKED.
  Parallelization: Wave 1 | Blocked by: 1,2 | Blocks: 5,6,10,11,12
  References: `GOVERNANCE.md:14-17`; `schema/mbras.schema.json:3-6`; `docs/PIBRAS-STANDARD-v0.2-draft.md:85-98,371-386`; `db/schema.sql:430-444,682-719`; `docs/VERSIONING.md:19-40`.
  Acceptance criteria: no non-exempt public artifact contains branded ID; exempt historical docs contain the exact banner within first 20 non-empty lines, not adjacency. Origin matches approved GitHub URL; schema/docs URLs match independently approved roots and same neutral identity.
  QA scenarios: mandatory task-3 QA script covers identity happy, missing-approval BLOCKED, and URL mutation; writes `.omo/evidence/task-3-manifest.json`.
  Commit: Y | `docs(governance): establish neutral contract authority`

- [ ] 4. Build red-first parity and domain-invariant harnesses
  What to do / Must NOT do: Create parity/invariant scripts, frozen `tests/contracts/pre-reconciliation/`, synthetic green `tests/contracts/aligned/`, pytest, and expected-red manifest. Manifest excludes identity rules, uses severity enum, never refreshes. Checks fail unresolved critical/high/medium; tests assert exact IDs.
  Parallelization: Wave 1 | Blocked by: 1,2 | Blocks: 5-9
  References: `schema/mbras.schema.json:607-620,759-773`; `types/mbras.ts:434-445,542-554`; `db/schema.sql:178-193,228-250,365-368,649-659,845-858`; `tests/golden/conformance-cases.json`; `mappings/v0.1.0-code-to-v0.2.md`.
  Acceptance criteria: harness pytest exits 0 while direct target checks emit expected red findings. No aggregate script exists yet; Todo 5 runs direct checks to green and Todo 9 later includes them.
  QA scenarios: mandatory task-4 QA script runs aligned green and frozen expected-red commands; writes `.omo/evidence/task-4-manifest.json`.
  Commit: Y | `test(contracts): add parity and invariant gates`

- [ ] 5. Reconcile v0.1.0 artifacts into one v0.2 release candidate contract
  What to do / Must NOT do: Apply `mappings/v0.1.0-code-to-v0.2.md` exhaustively across normative docs, JSON Schema, Zod, DDL, OpenAPI, samples, golden JSON fixtures, and the existing `portal-feed.valid.xml` XML surface. Resolve every parity finding, including ExposureRule identifier semantics, JavaScript-safe AuditEvent IDs as decimal strings at JSON/TS boundaries, constrained DDL change type, WGS84 checks, and Property/Unit building coherence. Prepare canonical v0.2 candidate entities while preserving documented aliases during the compatibility window. Produce `docs/migrations/v0.1.0-to-v0.2.md` with examples, classification, rollback, and experimental exclusions. Label every output candidate/draft until Todo 10 records real acceptance. Do not silently promote future product entities.
  Parallelization: Wave 2 | Blocked by: 2,3,4 | Blocks: 6-12
  References: `mappings/v0.1.0-code-to-v0.2.md`; `docs/VERSIONING.md:37-63`; `README.md:25-42`; all findings emitted by Todo 4.
  Acceptance criteria: root parity/invariants exit 0; compatibility validates; migration maps every mapping row plus every expected-red ID exactly once; missing/duplicate fails; report contains no critical/high/medium finding.
  QA scenarios: mandatory task-5 QA script runs conformance/types/parity/invariants and direct disposable drift checks; mutation runner is deferred to Todo 8. Writes `.omo/evidence/task-5-manifest.json`.
  Commit: Y | `feat(standard): reconcile v0.2 contract surfaces`

- [ ] 6. Complete the secured OpenAPI reference projection
  What to do / Must NOT do: Expand `openapi.yaml` and `validate_openapi.py` so required paths include Unit, Property, Listing, Property ExposurePolicy, and conformance cases. Add bearer authentication, global or operation-level security, 401/403 responses, shared error schemas, operation IDs, path-parameter validation, and canonical external JSON Schema refs. Add OpenAPI fixtures/assertions for missing auth and policy denial; this is a reference contract only, not an auth server implementation.
  Parallelization: Wave 2 | Blocked by: 5 | Blocks: 8-12 | Can parallelize with: 7
  References: `README.md:47-48`; `openapi.yaml:19-155`; `scripts/validate_openapi.py:31-35`; `docs/lgpd.md:32-34`; `docs/exposure-policy.md`.
  Acceptance criteria: `uv run scripts/validate_openapi.py` and pinned `uv run openapi-spec-validator openapi.yaml` both exit 0; all five surfaces/security/errors are tested; every external ref uses approved root.
  QA scenarios: mandatory task-6 QA script runs both validators and disposable API mutations; writes `.omo/evidence/task-6-manifest.json`.
  Commit: Y | `feat(openapi): secure and complete reference surface`

- [ ] 7. Add identical local and CI PostgreSQL 16 validation
  What to do / Must NOT do: Require Docker/Linux/ubuntu. Use deterministic container prefix `pibras-db-check-<pid>-<random>`. Add transaction precheck; run outer-transaction DDL and rollback assertion. Add catalog/negative assertions/cleanup. Docker absence exits 2.
  Parallelization: Wave 2 | Blocked by: 2,4,5 | Blocks: 9,10,12 | Can parallelize with: 6
  References: `db/schema.sql:1-17` and complete DDL; domain constraints from Todo 5; `AGENTS.md` RTK command rule applies to execution orchestration, not script contents.
  Acceptance criteria: `scripts/db_check.sh` exits 0 twice consecutively; a syntax mutation and each key constraint mutation exit non-zero; `docker ps -a` contains no PIBRAS check container afterward.
  QA scenarios: mandatory task-7 QA script runs PostgreSQL happy/failure/cleanup; writes `.omo/evidence/task-7-manifest.json`.
  Commit: Y | `test(db): validate DDL on PostgreSQL 16`

- [ ] 8. Expand conformance, policy evaluation, and mutation killing
  What to do / Must NOT do: Extend conformance. Todo-8 mutation categories are exactly `json-format`, `xml`, `zod`, `policy`, `projection`, `openapi`, `ddl`, and `migration`, at least one each; `release-metadata`, `license`, `checksum` are excluded until Todo 11. DDL enables Docker/no network; others default both false. Runner isolates entries.
  Parallelization: Wave 2 | Blocked by: 5,6,7 | Blocks: 9,10,12
  References: `scripts/validate_conformance.py:140-203,234-342`; `tests/golden/`; `tests/golden/conformance-cases.json`; `docs/PIBRAS-STANDARD-v0.2-draft.md:675-698`; `docs/exposure-policy.md`.
  Acceptance criteria: conformance and `uv run scripts/run_mutations.py --report .omo/evidence/task-8-mutations.json` exit 0; every active category has a killed mutant; status clean.
  QA scenarios: mandatory task-8 QA script covers golden/mutations/survivor failure; writes `.omo/evidence/task-8-manifest.json` referencing mutation report.
  Commit: Y | `test(conformance): enforce policy and mutation coverage`

- [ ] 9. Make one aggregate local gate and mirror it in CI
  What to do / Must NOT do: Create `security/.secrets.baseline`, `security/secrets-review.yaml` (reviewer/date/baseline hash), and `scripts/check_secrets.py`; clean scan exits 0 and seeded fake secret exits 1. Create the audit policy and aggregate; the aggregate must invoke both `npm run typecheck` and `npm run test:types` as distinct required gates, plus every Python, OpenAPI, conformance, mutation, and PostgreSQL gate delivered by Todos 2-8. Land the exact pinned `quality` workflow through the bootstrap PR, then configure/read back protection requiring quality/PR/linear history/no force push/delete. Missing GitHub API/admin/network is BLOCKED.
  Parallelization: Wave 3 sequential | Blocked by: 6,7,8 | Blocks: 10,12
  References: outputs of Todos 2,4,6-8; `README.md:70-75`; `docs/REPOSITORY.md` from Todo 1.
  Acceptance criteria: Todo-9 phase set/report pass; workflow has one aggregate invocation, full pins, Docker/tag fetch/evidence; branch-protection readback shows required `quality`, PR review, no force push/delete. Todo 11 later proves final phase completeness.
  QA scenarios: mandatory task-9 QA script runs aggregate twice and invalid-UUID failure; writes `.omo/evidence/task-9-manifest.json`.
  Commit: Y | `ci(quality): mirror the canonical local gate`

- [ ] 10. Make governance, LGPD, and security executable
  What to do / Must NOT do: Add RFC/security/contribution/code-of-conduct/changelog artifacts and amend policy per schema. Governance checker validates them. Plan-evidence checker accepts only explicit `--evidence <dist-path>` in release checks; local F1 may point to `.omo`, but CI mode never does. Create authoritative scope-policy enumerating permitted paths/surfaces added after `pibras-baseline` and forbidden product surfaces. Add governance structural and scope phases to aggregate. Todo 10 completion requires standalone Accepted mode exit 0.
  Parallelization: Wave 3 sequential | Blocked by: 6-9 | Blocks: 11,12
  References: `GOVERNANCE.md`; `RFC_PROCESS.md`; `docs/VERSIONING.md`; `docs/lgpd.md`; `docs/entity-resolution.md`; `docs/exposure-policy.md`; migration report from Todo 5.
  Acceptance criteria: before approval standalone exits `RFC_NOT_ACCEPTED` while aggregate structural mode passes; after real maintainer approval standalone exits 0 and Todo 10 may complete; every authority/status link resolves.
  QA scenarios: mandatory task-10 QA script covers accepted governance and missing-section failures; writes `.omo/evidence/task-10-manifest.json`.
  Commit: Y | `docs(governance): formalize v0.2 acceptance and security`

- [ ] 11. Replace the license stub only after legal approval and define public packaging
  What to do / Must NOT do: Legal record approves Apache source `https://www.apache.org/licenses/LICENSE-2.0.txt`, SHA-256 `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`, and CC source `https://creativecommons.org/licenses/by/4.0/legalcode.txt`, SHA-256 `9ba9550ad48438d0836ddab3da480b3b69ffa0aac7b7878b5a0039e7ab429411`, with retrieval timestamps; commit exact bytes. Apply mapping/SPDX, set candidate artifact version, create `scripts/build_release.sh`, release/artifact checker, `scripts/hash_release_sources.py`, `scripts/compare_release.py`, `scripts/record_tag_evidence.sh`, and tracked `governance/final-release-allowlist.yaml` containing only the final-only differences enumerated in F5; append structural release-policy phase to `--mode ci`. `build_release.sh` creates payload, artifact manifest, checksums, and detached signature; pretag/posttag are validation-only and never mutate a bundle. Todo 11 does not run pretag/posttag modes because no bundle/tag exists. Append deferred mutants and require them killed.
  Parallelization: Wave 3 sequential | Blocked by: 3,5,10 and recorded accepted RFC | Blocks: 12
  References: `LICENSE:1-8`; `GOVERNANCE.md:29-34`; `docs/VERSIONING.md`; neutral identity decision from Todo 3.
  Acceptance criteria: before legal approval the standalone legal-policy check fails; after approval hashes/SPDX/deferred mutants pass and `scripts/check_all.sh --mode ci --report .artifacts/check-all-todo11.json` exits 0 through `legal_approved`. The `rc` and `final` phases remain intentionally inapplicable until Todo 12 and F5.
  QA scenarios: mandatory task-11 QA script covers license happy/truncation/mapping failure; writes `.omo/evidence/task-11-manifest.json`.
  Commit: Y | `docs(license): adopt approved dual licensing`

- [ ] 12. Produce and sign the initial v1.0.0 release candidate (`RC_ARTIFACT_VERSION=1.0.0-rc.1`, `RC_TAG=v1.0.0-rc.1`)
  What to do / Must NOT do: Run signing verification and set v1 fields. Copy completed Todo 1-11 manifests and only their artifacts marked `bundle: true`; do not bundle the incomplete Todo-12 manifest or either Todo-12 report. Write pretag report to exact external `.omo/evidence/task-12-pretag.json` and posttag report to exact external `.omo/evidence/task-12-posttag.json`, both `bundle: false` in the eventual Todo-12 manifest. Bundle metadata records only `source_snapshot_sha` from `scripts/hash_release_sources.py`, never a branch commit SHA or self-containing full-tree hash. Build/run pretag on branch; rebase-merge, assert branch/main source-snapshot equality and manifest `source_snapshot_sha` equals a fresh hash at main, rerun pretag without regenerating or mutating the bundle, create tag/posttag/push. Failed tag remains unpushed/deleted; increment RC.
  Parallelization: Wave 3 final | Blocked by: 9-11 | Blocks: F1-F4
  References: `docs/VERSIONING.md:19-63`; accepted RFC; `docs/REPOSITORY.md`; `governance/release-policy.yaml`; all prior evidence.
  Acceptance criteria: pretag and posttag aggregates exit 0 in order; both exact Todo-12 reports and the completed Todo-12 manifest remain external; bundle manifest/checksums/detached signature/tag verification succeed without any post-hash bundle mutation.
  QA scenarios: `scripts/qa/task-12.sh --rc-version "${RC_ARTIFACT_VERSION}" --report .omo/evidence/task-12-manifest.json` performs unpacked happy checks and tamper failure. Evidence paths are exactly external `.omo/evidence/task-12-pretag.json`, `.omo/evidence/task-12-posttag.json`, and canonical `.omo/evidence/task-12-manifest.json`; the manifest records hashes for both reports with `bundle: false`.
  Commit: Y | `release: prepare PIBRAS ${RC_ARTIFACT_VERSION}`

## Final verification wave
> F1-F4 run after all Todos and all external gates except final-promotion approval. ALL must APPROVE; F5 is separate after explicit confirmation.
> F1 runs in the originating release workspace so it can receive the explicit untracked posttag evidence handoff. F2-F4 use independent RC clones. Every verifier uses temporary `GNUPGHOME`, imports the tracked public key, checks fingerprint, and verifies the RC tag; missing trust material is BLOCKED.
- [ ] F1. Plan compliance audit
  In origin, where `$ORIGIN_EVIDENCE_DIR` is exactly `$(pwd)/.omo/evidence`, run `scripts/check_all.sh --mode release-posttag --bundle "$RC_BUNDLE" --evidence "$RC_BUNDLE/evidence" --tag "$RC_TAG" --fingerprint <approved-fingerprint> --external-evidence .omo/evidence/task-12-posttag.json --report .omo/evidence/final-f1-release-posttag.json`, then `uv run scripts/check_plan_evidence.py --plan docs/plans/pibras-10-of-10-public-standard.md --lock governance/plan-lock.json --evidence .omo/evidence --through 12 --report .omo/evidence/final-f1-plan-evidence.json` and `git verify-tag "$RC_TAG"`; write exact `$ORIGIN_EVIDENCE_DIR/final-f1-plan-compliance.md` with APPROVE and record its SHA-256 alongside F2-F4 receipts.
- [ ] F2. Code quality review
  In an independent clone, run `scripts/check_all.sh --mode ci --report .omo/evidence/final-f2-check-all.json` and `uv run scripts/check_ci_pins.py --verify-upstream`. Network outage is BLOCKED. Write exact `final-f2-code-quality.md` schema and APPROVE, then atomically copy it to `$ORIGIN_EVIDENCE_DIR/final-f2-code-quality.md` and return its SHA-256.
- [ ] F3. Independent agent-executed QA
  Clone `${RC_TAG}`, run CI aggregate, then `scripts/qa/task-5.sh --negative-only`, `scripts/qa/task-6.sh --negative-only`, `scripts/qa/task-7.sh --negative-only`, `scripts/qa/task-8.sh --negative-only`, and `scripts/qa/task-12.sh --rc-version "${RC_ARTIFACT_VERSION}" --negative-only`; all expected failure assertions pass. Write `final-f3-independent-qa.md` and APPROVE, then atomically copy it to `$ORIGIN_EVIDENCE_DIR/final-f3-independent-qa.md` and return its SHA-256.
- [ ] F4. Scope fidelity
  In independent clone run `git diff --name-status pibras-baseline.."$RC_TAG"`, `git ls-tree -r --name-only "$RC_TAG"`, `uv run scripts/check_secrets.py --baseline security/.secrets.baseline`, and `uv run scripts/check_scope.py --policy governance/scope-policy.yaml --baseline pibras-baseline --tag "$RC_TAG"`; write clone-local `.omo/evidence/final-f4-scope-fidelity.md` with required schema and APPROVE, then atomically copy that file to `$ORIGIN_EVIDENCE_DIR/final-f4-scope-fidelity.md` and return the origin copy's SHA-256.

### Sequential promotion after the final verification wave
- [ ] F5. Promote the approved immutable RC to v1.0.0
  Gate on explicit user input, then create/validate `governance/final-promotion-approval.yaml` as the first and only change under `governance/`; later version-field and derived-file updates occur only under `dist/pibras-1.0.0/`. This file carries the required `final_artifact_version: 1.0.0`. Copy the four exact F1-F4 files from `$ORIGIN_EVIDENCE_DIR` into `dist/pibras-1.0.0/evidence/` and include their hashes. Rebuild from RC with normative hashes identical. Allowed differences are `governance/final-promotion-approval.yaml`, final version fields in release metadata/artifact manifest, the four verifier evidence files, and necessarily regenerated `artifact-manifest.json`, `CHECKSUMS.txt`, and `CHECKSUMS.txt.asc`; the allowlist distinguishes semantic inputs from these derived outputs and the comparison checker recomputes all three. Run, in order: `scripts/build_release.sh --version 1.0.0 --source-rc "$RC_BUNDLE" --output dist/pibras-1.0.0 --fingerprint <approved-fingerprint>`; `uv run scripts/compare_release.py --rc-bundle "$RC_BUNDLE" --final-bundle dist/pibras-1.0.0 --allow-policy governance/final-release-allowlist.yaml --report .omo/evidence/final-f5-compare.json`; `scripts/check_all.sh --mode release-pretag --bundle dist/pibras-1.0.0 --evidence dist/pibras-1.0.0/evidence --tag v1.0.0 --fingerprint <approved-fingerprint> --report .omo/evidence/final-f5-pretag.json`; and `scripts/check_all.sh --mode ci --report .omo/evidence/final-f5-technical.json`. Rebase-merge the single F5 commit onto the reviewed RC commit, assert final branch/main source-snapshot equality, create signed local tag `v1.0.0`, run `scripts/record_tag_evidence.sh --tag v1.0.0 --fingerprint <approved-fingerprint> --output .omo/evidence/final-f5-posttag.json`, then run `scripts/check_all.sh --mode release-posttag --bundle dist/pibras-1.0.0 --evidence dist/pibras-1.0.0/evidence --tag v1.0.0 --fingerprint <approved-fingerprint> --external-evidence .omo/evidence/final-f5-posttag.json --report .omo/evidence/final-f5-release-posttag.json` followed by `git verify-tag v1.0.0`; push commit/tag only after PASS. A transient tag/check failure deletes the unpushed tag and retries on the unchanged F5 commit. A content fix abandons that final candidate, returns to a newly reviewed incremented RC, and creates exactly one new F5 commit atop that new RC.

## Commit strategy
- One independently reviewable commit per todo using the exact subjects above; never combine external approval metadata with unrelated contract changes.
- Todo 1 creates baseline/main then local-only `release/pibras-v1`; Todos 2-8 work there. Todo 3 configures origin and pushes main, baseline tag, and release branch. Todo 9 bootstrap PR rebase-merges Todos 1-9, then enables protection. Todo 10 starts from protected main and is rebase-merged by PR before Todo 11 branches; Todo 11 likewise rebase-merges before Todo 12 branches from the resulting protected main. Todo 12 branch is `release/v${RC_ARTIFACT_VERSION}` and tag `${RC_TAG}`; F5 uses `release/v1.0.0`. All merges rebase-only/linear; tags point to exact main commits.
- Keep the worktree clean between todos. Generated evidence under `.omo/` stays untracked; only finalized `dist/.../evidence` enters the release commit.
- Never amend or force-push an already reviewed RC/release commit; fixes produce a new commit and incremented RC tag.
- Todos 1-8 push only after their todo-specific gates because aggregate does not exist. Todo 9 onward push only after aggregate PASS and merge through protected main as defined above.

## Success criteria
- C0: Git baseline is clean, local state ignored, neutral remote configured only after approval, and branch/release policy documented.
- C1: `uv run scripts/check_domain_invariants.py` exits 0 and rejects inconsistent building, identity, money, and policy cases.
- C2: `uv run scripts/check_governance.py` exits 0 with a genuinely accepted RFC and complete LGPD/security/rollback data.
- C3: `uv run scripts/check_parity.py`, `npm run typecheck`, `npm run test:types`, repository OpenAPI validator, and pinned official OpenAPI validator exit 0 with no known drift.
- C4: conformance passes and every declared mutation is killed without changing the worktree.
- C5: clean-clone installs are lockfile-only; `scripts/check_all.sh --mode ci --report .artifacts/check-all.json` passes locally and is the sole CI command.
- C6: approved complete licenses, neutral identity, signed tags, checksums, release bundle, changelog, RFC, and evidence pass `check_release.py`.
- F1-F4 return `APPROVE`, the user explicitly confirms promotion, and F5 verifies the signed final tag; any missing external legal, maintainer, identity, signing, or final-user approval keeps the release explicitly blocked rather than lowering the gate.
