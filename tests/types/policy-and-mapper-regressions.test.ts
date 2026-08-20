/**
 * Regression suite for defects found by independent review of the reference
 * implementation (PR #4). Each test reproduces a specific defect and is written
 * to fail against the pre-fix code, so the conformance suite gains the negative
 * coverage it previously lacked.
 */

import { test } from "node:test";
import assert from "node:assert/strict";
import { authorize, OPERATOR_BRAND } from "../../src/index.ts";
import {
  ExposurePolicyEvaluator,
  parseAreaM2,
  ZapXMLMapper,
  computePayloadDigest,
} from "../../src/index.ts";
import type { ExposurePolicy } from "../../types/mbras.ts";

const TIMESTAMP = "2026-01-01T00:00:00Z";

function policy(overrides: Partial<ExposurePolicy> = {}): ExposurePolicy {
  return {
    id: "11111111-1111-4111-8111-111111111111",
    tenant_id: null,
    resource_type: "property",
    resource_id: null,
    exposure_level: "restricted",
    rules: [],
    requires_approval_for: [],
    allowed_channels: ["portal"],
    default_decision: "deny",
    audit_sensitive_reads: true,
    created_at: TIMESTAMP,
    updated_at: TIMESTAMP,
    ...overrides,
  } as ExposurePolicy;
}

/* ------------------------------------------------------------------ *
 * Defect 2: an allow rule's `fields` allowlist was ignored, so
 * projection behaved as a deny-list and leaked restricted fields.
 * ------------------------------------------------------------------ */

test("projectForChannel honours the allow rule field allowlist", () => {
  const result = ExposurePolicyEvaluator.projectForChannel({
    property: {
      id: "3f2504e0-4f89-41d3-9a0c-0305e82c3301",
      headline: "Cobertura",
      asking_price: { amount: 9_999_900, currency: "BRL" },
      matricula: "123.456",
    } as never,
    unit: null,
    media_assets: [],
    policy: policy({
      rules: [
        {
          id: "r-allow-headline",
          priority: 1,
          effect: "allow",
          actions: ["publish"],
          fields: ["headline"],
          roles: ["*"],
          conditions: {},
          reason_code: null,
        },
      ],
    }),
    context: { action: "publish", channel_type: "portal", caller_role: "public" },
  });

  assert.notEqual(result, null, "an allow rule must produce a projection");
  const emitted = Object.keys(result!.property);
  // `id` is always retained as the resource handle; nothing else outside the
  // allowlist may survive.
  assert.deepEqual(emitted.sort(), ["headline", "id"]);
  assert.ok(!("matricula" in result!.property), "matricula must never reach a portal channel");
  assert.ok(!("asking_price" in result!.property), "price is outside the allowlist");
});

/* ------------------------------------------------------------------ *
 * Defect 3: `needs_approval` fell through as publishable because only
 * `deny` returned null.
 * ------------------------------------------------------------------ */

test("projectForChannel blocks needs_approval as unpublishable", () => {
  const result = ExposurePolicyEvaluator.projectForChannel({
    property: {
      id: "3f2504e0-4f89-41d3-9a0c-0305e82c3302",
      asking_price: { amount: 9_999_900, currency: "BRL" },
    } as never,
    unit: null,
    media_assets: [],
    policy: policy({ default_decision: "needs_approval" }),
    context: { action: "publish", channel_type: "portal", caller_role: "public" },
  });

  assert.equal(result, null, "needs_approval must not be emitted without approval");
});

test("projectForChannel blocks when the action requires prior approval", () => {
  const result = ExposurePolicyEvaluator.projectForChannel({
    property: { id: "3f2504e0-4f89-41d3-9a0c-0305e82c3303" } as never,
    unit: null,
    media_assets: [],
    policy: policy({ requires_approval_for: ["publish"] }),
    context: { action: "publish", channel_type: "portal", caller_role: "public" },
  });

  assert.equal(result, null);
});

/* ------------------------------------------------------------------ *
 * Defect 4: the area regex stripped every literal digit `2`.
 * ------------------------------------------------------------------ */

test("CSV area parsing preserves digits that collide with the unit suffix", () => {
  const rows: Array<[string, number]> = [
    ["120 m2", 120],
    ["250", 250],
    ["2", 2],
    ["1234 m²", 1234],
    ["320,5", 320.5],
    ["1.250 m2", 1250],
  ];
  for (const [input, expected] of rows) {
    const parsed = parseAreaM2(input);
    assert.equal(parsed, expected, `area ${JSON.stringify(input)} must parse to ${expected}`);
  }
});

/* ------------------------------------------------------------------ *
 * Defect 5: the street number was reused as unit_number, collapsing
 * every apartment at one address onto a single dedupe key.
 * ------------------------------------------------------------------ */

test("ZAP mapper does not use the street number as the unit number", () => {
  const xml = `<Imovel>
    <CodigoImovel>A1</CodigoImovel>
    <TipoImovel>Apartamento</TipoImovel>
    <Endereco>Rua Exemplo</Endereco>
    <Numero>500</Numero>
    <Complemento>Apto 71</Complemento>
    <Bairro>Jardins</Bairro>
    <Cidade>São Paulo</Cidade>
    <UF>SP</UF>
    <PrecoVenda>1000000</PrecoVenda>
  </Imovel>`;

  const mapped = ZapXMLMapper.mapXmlItem(xml);
  assert.notEqual(
    mapped.unit.unit_number,
    "500",
    "street number must not be promoted to unit_number",
  );
});

test("ZAP mapper gives distinct dedupe keys to distinct units at one address", () => {
  const build = (complement: string, code: string) => `<Imovel>
    <CodigoImovel>${code}</CodigoImovel>
    <TipoImovel>Apartamento</TipoImovel>
    <Endereco>Rua Exemplo</Endereco>
    <Numero>500</Numero>
    <Complemento>${complement}</Complemento>
    <Bairro>Jardins</Bairro>
    <Cidade>São Paulo</Cidade>
    <UF>SP</UF>
    <PrecoVenda>1000000</PrecoVenda>
  </Imovel>`;

  const first = ZapXMLMapper.mapXmlItem(build("Apto 71", "A1"));
  const second = ZapXMLMapper.mapXmlItem(build("Apto 82", "A2"));

  assert.notEqual(
    first.unit.dedupe_key,
    second.unit.dedupe_key,
    "different apartments at one address must not share a dedupe key",
  );
});

/* ------------------------------------------------------------------ *
 * Defect 6 (non-blocking): the payload digest ignored nested values.
 * ------------------------------------------------------------------ */

test("payload digest distinguishes payloads differing only in nested values", () => {
  const a = computePayloadDigest({ id: 1, nested: { price: 100 } });
  const b = computePayloadDigest({ id: 1, nested: { price: 999_999 } });
  assert.notEqual(a, b, "nested differences must change the digest");
});

test("payload digest is stable across key ordering", () => {
  const a = computePayloadDigest({ id: 1, nested: { price: 100, currency: "BRL" } });
  const b = computePayloadDigest({ nested: { currency: "BRL", price: 100 }, id: 1 });
  assert.equal(a, b, "digest must be order-independent");
});

/* ------------------------------------------------------------------ *
 * Defect 1: routes accepted unauthenticated requests despite the
 * bearer-auth contract in openapi.yaml.
 * ------------------------------------------------------------------ */

test("authorize rejects a request with no bearer credential", () => {
  const result = authorize({ headers: {} } as never);
  assert.equal(result.ok, false);
  assert.equal(result.ok === false && result.status, 401);
});

test("authorize rejects a malformed authorization header", () => {
  const result = authorize({ headers: { authorization: "Basic abc" } } as never);
  assert.equal(result.ok, false);
  assert.equal(result.ok === false && result.status, 401);
});

test("authorize rejects an incorrect bearer token", () => {
  const previous = process.env["PIBRAS_API_TOKEN"];
  process.env["PIBRAS_API_TOKEN"] = "correct-token-value";
  try {
    const result = authorize({ headers: { authorization: "Bearer wrong-token-value" } } as never);
    assert.equal(result.ok, false);
    assert.equal(result.ok === false && result.status, 403);
  } finally {
    if (previous === undefined) delete process.env["PIBRAS_API_TOKEN"];
    else process.env["PIBRAS_API_TOKEN"] = previous;
  }
});

test("authorize accepts the configured bearer token", () => {
  const previous = process.env["PIBRAS_API_TOKEN"];
  process.env["PIBRAS_API_TOKEN"] = "correct-token-value";
  try {
    const result = authorize({ headers: { authorization: "Bearer correct-token-value" } } as never);
    assert.equal(result.ok, true);
  } finally {
    if (previous === undefined) delete process.env["PIBRAS_API_TOKEN"];
    else process.env["PIBRAS_API_TOKEN"] = previous;
  }
});

test("authorize fails closed when the server has no token configured", () => {
  const previous = process.env["PIBRAS_API_TOKEN"];
  delete process.env["PIBRAS_API_TOKEN"];
  try {
    const result = authorize({ headers: { authorization: "Bearer anything" } } as never);
    assert.equal(result.ok, false, "no configured token must not mean open access");
    assert.equal(result.ok === false && result.status, 403);
  } finally {
    if (previous !== undefined) process.env["PIBRAS_API_TOKEN"] = previous;
  }
});

/* Defect 8: the watermark placeholder had no runtime substitution. */

test("OPERATOR_BRAND resolves to a real value, not a placeholder", () => {
  assert.ok(!OPERATOR_BRAND.includes("{{"), "brand must not be an unsubstituted placeholder");
  assert.ok(OPERATOR_BRAND.length > 0);
});

/* ------------------------------------------------------------------ *
 * ReDoS: a variante anterior do parser de área retrocedia de forma
 * polinomial em entrada adversária vinda de CSV não confiável.
 * ------------------------------------------------------------------ */

test("area parsing stays linear on adversarial whitespace", () => {
  const hostile = `1${" ".repeat(50_000)}m2x`;
  const started = process.hrtime.bigint();
  parseAreaM2(hostile);
  const elapsedMs = Number(process.hrtime.bigint() - started) / 1e6;
  assert.ok(elapsedMs < 100, `parsing took ${elapsedMs.toFixed(1)}ms; expected linear behaviour`);
});

test("area parsing tolerates internal whitespace", () => {
  assert.equal(parseAreaM2(" 1.250  m2 "), 1250);
  assert.equal(parseAreaM2("120m²"), 120);
});
