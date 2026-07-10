# PIBRAS Repository Policy

## Local bootstrap

The repository is initialized locally with `git init` on branch `main`. No remote is
configured at bootstrap time. `.omo/`, `.codegraph`, `.artifacts/`, caches, secrets,
and other local agent state are excluded via `.gitignore` and must never be tracked.

The approved execution plan is tracked byte-for-byte at
`docs/plans/pibras-10-of-10-public-standard.md`. Its SHA-256 is locked in
`governance/plan-lock.json`. The tracked plan is immutable approved input: no Todo
or gate checkbox in it is ever edited. Execution state lives exclusively in
`.omo/evidence/task-<N>-manifest.json` files (untracked local evidence), never in
Markdown checkboxes.

## Baseline tag

The first commit on `main` (`chore(repo): establish PIBRAS baseline`) is marked with
the annotated tag `pibras-baseline`. All subsequent work is measured against this
baseline.

## Branch topology

- `main` — the integration branch. Protected once a remote exists.
- `release/pibras-v1` — local-only release branch created at the baseline. It tracks
  release-candidate preparation and is pushed only after the neutral remote exists.
- Short-lived task branches may be used locally; they merge into `main` rebase-only.

## Deferred neutral remote

Per `GOVERNANCE.md`, the standard must be published under a neutral public identity.
No remote is configured or pushed at bootstrap. The remote is added only in Todo 3,
after the neutral organization/identity is explicitly approved by the owner. Until
then all work is local; nothing in the repository may embed a non-neutral
organization identity in URLs, schema `$id`s, or documentation.

## Protected-main transition

When the neutral remote is configured (Todo 3), `main` becomes protected:

- No direct pushes; changes land via reviewed merges.
- Rebase-only merges (linear history; no merge commits).
- Tags are created locally, verified, then pushed explicitly.

## Rebase-only merges

All integration into `main` uses rebase (fast-forward) semantics. Merge commits are
not permitted; history stays linear so that evidence manifests and tags map 1:1 to
commits.

## RC / final tag policy

- Release candidates: annotated tags `v<MAJOR>.<MINOR>.<PATCH>-rc.<N>`.
- Final releases: annotated tags `v<MAJOR>.<MINOR>.<PATCH>`.
- A final tag is created only after all release gates (F1–F5) pass and the RC bundle
  evidence is complete. Tags are never moved or deleted; a bad tag is superseded by
  the next RC/patch tag.
- Pre/post-tag evidence for the release Todo remains external to the RC bundle, as
  defined by the plan's verification strategy.
