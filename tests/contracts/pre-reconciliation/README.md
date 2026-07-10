# Pre-reconciliation fixtures (FROZEN — never refresh)

Historical snapshot of the contract drift and entity inconsistencies that
existed before reconciliation. These fixtures are **explicitly frozen**: they
must NEVER be regenerated from the live contracts or datasets. They exist so
the parity/invariant checkers can be asserted red-first against a stable,
known-bad input.

Expected findings (asserted exactly by `tests/contracts/test_gates.py` via
`tests/contracts/expected-red-manifest.json`):

- `PIBRAS-PAR-001` (high) — `AuditEvent.change_type` required in schema/types, nullable in SQL
- `PIBRAS-PAR-002` (medium) — `change_type` enum in schema/types, plain `TEXT` in SQL
- `PIBRAS-PAR-003` (medium) — `trust_tier` bounded 1..6 in schema, no SQL `CHECK`
- `PIBRAS-PAR-004` (medium) — `exposure_rule.field_visibility` `NOT NULL` in SQL, not required/defaulted in schema
- `PIBRAS-INV-001` (critical) — Property references a non-existent Unit
- `PIBRAS-INV-002` (high) — Property.building_id mismatches its Unit.building_id
- `PIBRAS-INV-003` (medium) — Unit references a non-existent Building

`PIBRAS-IDN-001` (identity rule) is also emitted by the invariant checker on
these fixtures but is **excluded** from the manifest and from blocking:
identity/dedupe reconciliation is out of scope for these gates.
