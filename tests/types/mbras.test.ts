import assert from "node:assert/strict"
import test from "node:test"

import {
  ConformanceTestCase,
  ExposurePolicy,
  Money,
  type ConformanceTestCase as ConformanceTestCaseValue,
  type ExposurePolicy as ExposurePolicyValue,
  type Money as MoneyValue,
} from "../../types/mbras.ts"

const UUID = "11111111-1111-4111-8111-111111111111"
const TIMESTAMP = "2026-07-10T00:00:00Z"

test("Money parses centavos when currency is canonical", () => {
  // Given: a canonical centavos money payload from the PIBRAS standard.
  const payload = { amount: 1_750_000_000, currency: "BRL" }

  // When: the TypeScript/Zod schema parses the payload.
  const parsed = Money.parse(payload)

  // Then: the observable parsed value preserves centavos and currency.
  const expected = { amount: 1_750_000_000, currency: "BRL" } satisfies MoneyValue
  assert.deepEqual(parsed, expected)
})

test("Money rejects fractional centavos", () => {
  // Given: a money payload with a fractional centavo amount.
  const payload = { amount: 10.5, currency: "BRL" }

  // When/Then: parsing fails because amount must be an integer.
  assert.throws(() => Money.parse(payload))
})

test("ExposurePolicy defaults to deny decisions", () => {
  // Given: an exposure policy payload without an explicit default_decision.
  const payload = {
    id: UUID,
    tenant_id: null,
    resource_type: "listing",
    resource_id: null,
    exposure_level: "restricted",
    created_at: TIMESTAMP,
    updated_at: TIMESTAMP,
  }

  // When: the TypeScript/Zod schema parses the payload.
  const parsed = ExposurePolicy.parse(payload)

  // Then: the parsed policy is default-deny and audits sensitive reads.
  const expected = {
    id: UUID,
    tenant_id: null,
    resource_type: "listing",
    resource_id: null,
    exposure_level: "restricted",
    rules: [],
    requires_approval_for: [],
    allowed_channels: [],
    default_decision: "deny",
    audit_sensitive_reads: true,
    created_at: TIMESTAMP,
    updated_at: TIMESTAMP,
  } satisfies ExposurePolicyValue
  assert.deepEqual(parsed, expected)
})

test("ConformanceTestCase defaults applies_to to an empty list", () => {
  // Given: the minimal conformance case index shape.
  const payload = {
    id: "money.centavos.expected",
    title: "Money is represented in centavos",
    version: "0.2",
    fixture_path: "tests/golden/money.centavos.expected.json",
    expected_result: "valid",
  }

  // When: the TypeScript/Zod schema parses the payload.
  const parsed = ConformanceTestCase.parse(payload)

  // Then: omitted applies_to becomes the deterministic empty list.
  const expected = {
    id: "money.centavos.expected",
    title: "Money is represented in centavos",
    version: "0.2",
    fixture_path: "tests/golden/money.centavos.expected.json",
    expected_result: "valid",
    applies_to: [],
  } satisfies ConformanceTestCaseValue
  assert.deepEqual(parsed, expected)
})
