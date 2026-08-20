import test from "node:test";
import assert from "node:assert/strict";
import { writeFileSync, unlinkSync } from "node:fs";
import { join } from "node:path";
import type { AddressInfo } from "node:net";
import {
  createPibrasApiServer,
  PibrasCLI,
  GenericCSVMapper,
} from "../../src/index.ts";
import type { ExposurePolicy } from "../../types/mbras.ts";

test("PIBRAS HTTP REST Server handles ingestion, dedupe, arbitration, and feeds", async () => {
  const server = createPibrasApiServer();
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const port = (server.address() as AddressInfo).port;
  const baseUrl = `http://127.0.0.1:${port}`;

  try {
    // 1. GET /health
    const healthRes = await fetch(`${baseUrl}/health`);
    assert.equal(healthRes.status, 200);
    const healthBody = (await healthRes.json()) as { status: string; version: string };
    assert.equal(healthBody.status, "ok");
    assert.equal(healthBody.version, "0.1.0");

    // 2. POST /api/v1/ingest/raw
    const rawRes = await fetch(`${baseUrl}/api/v1/ingest/raw`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_system: "kenlo",
        payload: { title: "Cobertura Triplex", price: 30000000 },
      }),
    });
    assert.equal(rawRes.status, 201);
    const rawBody = (await rawRes.json()) as { success: boolean; data: { payload_sha256: string } };
    assert.equal(rawBody.success, true);
    assert.ok(rawBody.data.payload_sha256.length === 64);

    // 3. POST /api/v1/ingest/csv-row
    const csvRowRes = await fetch(`${baseUrl}/api/v1/ingest/csv-row`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        row: {
          rua: "Avenida Europa",
          numero: "500",
          bairro: "Jardim Europa",
          valor: 15000000,
          area_util: 450,
        },
      }),
    });
    assert.equal(csvRowRes.status, 201);
    const csvRowBody = (await csvRowRes.json()) as {
      success: boolean;
      data: { property: { asking_price: { amount: number } } };
    };
    assert.equal(csvRowBody.data.property.asking_price.amount, 1500000000);

    // 4. POST /api/v1/dedupe/match
    const { unit: candidateUnit } = GenericCSVMapper.mapRow({
      rua: "Avenida Europa",
      numero: "500",
      bairro: "Jardim Europa",
      matricula: "112233",
    });

    const matchRes = await fetch(`${baseUrl}/api/v1/dedupe/match`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        incoming_unit: candidateUnit,
        existing_inventory: [
          {
            id: "unit-999",
            matricula: "112233",
          },
        ],
      }),
    });
    assert.equal(matchRes.status, 200);
    const matchBody = (await matchRes.json()) as {
      success: boolean;
      data: { confidence: number; review_state: string };
    };
    assert.equal(matchBody.data.confidence, 1.0);
    assert.equal(matchBody.data.review_state, "auto_matched");

    // 5. POST /api/v1/feeds/portal
    const policy: ExposurePolicy = {
      id: "00000000-0000-0000-0000-000000000099",
      tenant_id: null,
      resource_type: "property",
      resource_id: candidateUnit.id,
      exposure_level: "public",
      rules: [
        {
          priority: 10,
          effect: "allow",
          actions: ["publish", "read"],
          fields: [],
          roles: ["portal_feed"],
          conditions: {},
          reason_code: null,
        },
      ],
      requires_approval_for: [],
      allowed_channels: ["portal"],
      default_decision: "deny",
      audit_sensitive_reads: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    const feedRes = await fetch(`${baseUrl}/api/v1/feeds/portal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        format: "pibras",
        items: [
          {
            property: GenericCSVMapper.mapRow({ rua: "Rua Seridó", valor: 25000000 }).property,
            unit: candidateUnit,
            policy,
          },
        ],
      }),
    });
    assert.equal(feedRes.status, 200);
    assert.equal(feedRes.headers.get("content-type"), "application/xml; charset=utf-8");
    const feedXml = await feedRes.text();
    assert.ok(feedXml.includes("<Listings>"));

    // 6. GET /unknown-path -> 404
    const notFoundRes = await fetch(`${baseUrl}/api/v1/non-existent`);
    assert.equal(notFoundRes.status, 404);
  } finally {
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
});

test("PibrasCLI executes batch CSV, Kenlo, and XML imports cleanly", () => {
  const tmpCsv = join(process.cwd(), "tests/tmp_test_import.csv");
  const tmpJson = join(process.cwd(), "tests/tmp_test_kenlo.json");

  try {
    // 1. CSV CLI Import
    writeFileSync(
      tmpCsv,
      "rua,numero,bairro,cidade,valor,area_util\nRua Oscar Freire,1000,Jardins,São Paulo,20000000,500\n",
      "utf-8"
    );
    const csvResult = PibrasCLI.runCsvImport(tmpCsv);
    assert.equal(csvResult.success, true);
    assert.equal(csvResult.total_processed, 1);

    // 2. Kenlo CLI Import
    writeFileSync(
      tmpJson,
      JSON.stringify([
        {
          codigo: "KL1010",
          tipo: "Cobertura",
          precoVenda: "R$ 32.000.000,00",
          endereco: { logradouro: "Rua Groelândia", bairro: "Jardim Europa" },
        },
      ]),
      "utf-8"
    );
    const kenloResult = PibrasCLI.runKenloImport(tmpJson);
    assert.equal(kenloResult.success, true);
    assert.equal(kenloResult.total_processed, 1);

    // 3. XML CLI Import with Golden feed
    const goldenXml = join(process.cwd(), "tests/golden/portal-feed.valid.xml");
    const xmlResult = PibrasCLI.runXmlImport(goldenXml);
    assert.equal(xmlResult.success, true);
    assert.equal(xmlResult.total_processed, 1);
  } finally {
    try {
      unlinkSync(tmpCsv);
    } catch {}
    try {
      unlinkSync(tmpJson);
    } catch {}
  }
});
