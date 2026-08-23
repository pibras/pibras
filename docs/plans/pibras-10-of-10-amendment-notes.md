# pibras-10-of-10-public-standard — Amendment Notes

> This file lives **beside** the locked plan, never inside it.
> `docs/plans/pibras-10-of-10-public-standard.md` is immutable approved input:
> its SHA-256 is pinned in `governance/plan-lock.json` and
> `scripts/check_plan_evidence.py` rejects any byte change. Corrections to the
> plan's prose are therefore recorded here, with a pointer to the affected
> text, so divergence between prose and executable contract stays discoverable
> without breaking the lock.

## Amendment 001 — RFC gate: one reviewable approval while single-maintainer

- **Recorded:** 2026-08-23
- **Effective:** 2026-08-21 (merged in PR #8, `5b82938`)
- **Approved by:** Ronaldo (owner)
- **Plan text affected:** "Execution invariants", release-policy phases bullet —
  states that `rfc_accepted` "additionally requires two maintainer approvals".

### What changed

| | Plan prose (locked, line 62) | Executable contract (authoritative) |
|---|---|---|
| Requirement | Two maintainer approvals | At least **one** rfc-gate approval (`minContains: 1` in `schema/release-policy.schema.json`) |
| Reviewability | Implicit in headcount | The approval must carry a non-empty immutable `review_reference`, enforced in code by `scripts/validate_release_policy.py` and pinned by `tests/contracts/test_release_policy.py` |

### Rationale

PIBRAS has a single maintainer; requiring two distinct approvers made formal
acceptance unsatisfiable by design — the gate could only ever be passed by
quietly weakening it, which is exactly the failure mode the gate exists to
prevent. This was instead relaxed deliberately and recorded: distinctness
across multiple approvers is not required while the project has one
maintainer. The `review_reference` requirement survives, so every acceptance
still points at something immutable and independently checkable (a PR URL,
commit, or minutes).

### Revisit condition

Reintroduce two-distinct-approver enforcement (`minContains: 2` plus a
distinctness check) if and when the maintainer group grows beyond one person.

### Divergence status

Until the plan is superseded per its own amendment procedure (new versioned
plan path + new lock hash + owner approval), this note — not the stale
sentence at line 62 — is the authority on how the rfc gate works. Note that
PR #8 already updated a *different* sentence of the same plan (the Todo 10
gate bullet, line ≈89) to single-maintainer language, so the locked plan now
contradicts itself internally: line 62 says two approvals, line 89 says one
reviewable approval. Line 89 matches the executable contract; line 62 is the
residual drift this amendment records.

### Related finding: plan lock is stale (pre-existing, discovered 2026-08-23)

- `governance/plan-lock.json` pins the **baseline** hash
  `3d9535f095831cb23a8c2b00df18f098889a3b89d3c6c484029811579df88368`
  (`locked_at: 2026-07-10T03:10:00Z`).
- The tracked plan changed twice after baseline without re-pinning:
  1. `c075ae1` — docs(governance): establish neutral contract authority
  2. `5b82938` / PR #8 — the Todo 10 gate bullet described above
- Live plan SHA-256 at HEAD `dfe3337`: `5ec73b315716131d9a07021c4a28549730d6463a93b1c4035512d04ff73a4c94`.
- `scripts/check_plan_evidence.py` (referenced by the plan's immutability
  invariant) does not exist yet, so nothing detects the mismatch today. Once
  built, it will fail on every invocation until the lock is reconciled.
- **Recommended remediation (owner decision):** ratify the two owner-approved
  merges by re-pinning the lock to the live hash with an updated `locked_at`
  and a pointer to this amendment file. Alternative: revert the plan to
  baseline bytes and carry every correction externally — not recommended,
  since the edits were approved and merged through normal review.
- Recorded here rather than fixed silently: updating a governance lock hash is
  itself a governance act and belongs to the owner.
- **Resolution (2026-08-23, owner-approved):** the owner ratified the two
  merged, owner-approved plan edits (`c075ae1`, `5b82938`) and the lock was
  re-pinned to the live hash
  `5ec73b315716131d9a07021c4a28549730d6463a93b1c4035512d04ff73a4c94`
  (`locked_at: 2026-08-23T18:20:00Z`). This amendment file remains the record
  of why the baseline hash and the ratified hash differ.
