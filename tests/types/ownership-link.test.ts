import assert from "node:assert/strict";
import test from "node:test";
import { Ownership } from "../../types/mbras.ts";

test("Ownership requires a party link", () => {
  const id = "11111111-1111-4111-8111-111111111111";
  const at = "2026-01-01T00:00:00Z";
  const link = {
    id, unit_id: "22222222-2222-4222-8222-222222222222",
    provenance: { source_system: "mbras_internal", trust_tier: 2, ingested_at: at },
    audit: { created_at: at, updated_at: at, version: 1, record_state: "active" },
  };
  assert.equal(Ownership.safeParse({ ...link, party_id: id }).success, true);
  assert.equal(Ownership.safeParse(link).success, false, "link without party_id accepted");
});
