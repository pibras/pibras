# Licence Applicability Map

> **Status:** **ADOPTED 2026-08-23** — owner-approved at the `legal` gate
> (`governance/release-policy.yaml`, phase `legal_approved`). The root
> `LICENSE` now carries the dual-licence notice; the verbatim texts live at
> `LICENSE-CODE` (Apache-2.0) and `LICENSE-DOCS` (CC BY 4.0). All three ⚠️
> boundary cases below were resolved as staged (Apache-2.0).

## Recommended split (from the LICENSE placeholder)

| Licence | Covers |
|---|---|
| Apache-2.0 | Code, schemas, SDKs, validators — technical artifacts |
| CC BY 4.0 | Documentation and specification text |

## Path mapping

| Paths | Licence | Rationale |
|---|---|---|
| `schema/*.json` | Apache-2.0 | Explicitly named as Apache-covered in the LICENSE placeholder ("schemas"). |
| `types/`, `db/`, `scripts/`, `tests/`, CI configs, manifests (`pyproject.toml`, `uv.lock`, `package.json`, `package-lock.json`) | Apache-2.0 | Executable code, DDL, validators, tooling. |
| `examples/`, `tests/golden/` | Apache-2.0 ⚠️ | Executable conformance corpus — treated as technical artifacts, not prose. Boundary case; confirm at adoption. |
| `docs/**` (all `.md`), root `*.md` (`README.md`, `GOVERNANCE.md`, `RFC_PROCESS.md`, `VERSIONING.md`), `mappings/*.md` | CC BY 4.0 | Documentation and normative prose. |
| `openapi.yaml` | Apache-2.0 ⚠️ | Machine-readable contract sitting beside `mbras.schema.json`; grouped with schemas rather than read as prose. Boundary case; the placeholder's "specification text" wording could also be read as CC BY 4.0. Confirm at adoption. |
| `governance/*.yaml`, `licenses/**` | Apache-2.0 ⚠️ | Policy/tooling metadata. Boundary case; confirm at adoption. |
| `LICENSE`, `LICENSE-CODE` (on adoption), `LICENSE-DOCS` (on adoption) | n/a | Licence texts themselves carry no copyright grant from this project. |

⚠️ = boundary judgment flagged during staging; **all three were confirmed as
Apache-2.0 by the owner at adoption (2026-08-23)**.

## Adoption record

The staged adoption procedure was executed on 2026-08-23:

1. Owner approved the split and the three ⚠️ boundary resolutions.
2. Root `LICENSE` replaced with the dual-licence notice; texts copied
   verbatim to `LICENSE-CODE` and `LICENSE-DOCS` (hashes match
   `PROVENANCE.json`).
3. Legal-gate approval appended to `governance/release-policy.yaml`;
   `phase: legal_approved`.
4. Verified via `scripts/validate_release_policy.py` and
   `tests/contracts/test_release_policy.py`.

## Provenance

Source URLs, retrieval timestamps, and SHA-256 hashes for both texts are
recorded in [`licenses/PROVENANCE.json`](PROVENANCE.json). Re-verify with:

```bash
shasum -a 256 licenses/Apache-2.0.txt licenses/CC-BY-4.0.txt
```
