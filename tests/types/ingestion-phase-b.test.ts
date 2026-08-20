import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import {
  DeadLetterQueue,
  KenloMapper,
  ZapXMLMapper,
  PollingScheduler,
} from "../../src/index.ts";
import { TRUST_TIERS } from "../../types/mbras.ts";

test("DeadLetterQueue enqueues failed payload and calculates exponential backoff", () => {
  const malformedPayload = { invalid_json: true, valor: "abc" };

  const dlqItem = DeadLetterQueue.enqueue({
    source_system: "kenlo",
    source_record_id: "BAD-123",
    raw_payload: malformedPayload,
    error_code: "SCHEMA_VALIDATION_ERROR",
    error: new Error("Valor must be numeric or valid BRL currency string"),
    max_retries: 3,
  });

  assert.equal(dlqItem.source_system, "kenlo");
  assert.equal(dlqItem.error_code, "SCHEMA_VALIDATION_ERROR");
  assert.equal(dlqItem.status, "quarantined");
  assert.equal(dlqItem.record_state, "rejected");
  assert.equal(dlqItem.retry_count, 0);
  assert.ok(dlqItem.next_retry_at !== null);

  // 1st retry failed
  const retry1 = DeadLetterQueue.recordRetryAttempt(dlqItem, new Error("Still failing"));
  assert.equal(retry1.retry_count, 1);
  assert.equal(retry1.status, "retrying");
  assert.ok(retry1.next_retry_at !== null);

  // 2nd retry failed
  const retry2 = DeadLetterQueue.recordRetryAttempt(retry1, new Error("Still failing"));
  assert.equal(retry2.retry_count, 2);
  assert.equal(retry2.status, "retrying");

  // 3rd retry failed -> exceeds max_retries (3) -> status: dropped
  const retry3 = DeadLetterQueue.recordRetryAttempt(retry2, new Error("Final failure"));
  assert.equal(retry3.retry_count, 3);
  assert.equal(retry3.status, "dropped");
  assert.equal(retry3.next_retry_at, null);

  // Successful retry resolution
  const resolved = DeadLetterQueue.recordRetryAttempt(dlqItem, null);
  assert.equal(resolved.status, "resolved");
  assert.equal(resolved.record_state, "active");
  assert.ok(resolved.resolved_at !== null);
});

test("KenloMapper transforms complete Kenlo webhook payload into canonical PIBRAS entities", () => {
  const kenloPayload = {
    codigo: "AP8899",
    tipo: "Apartamento",
    finalidade: "Venda",
    status: "Ativo",
    precoVenda: "R$ 22.000.000,00",
    valorCondominio: "R$ 14.500,00",
    valorIptu: "R$ 80.000,00",
    areaUtil: 620,
    areaTotal: 850,
    quartos: 4,
    suites: 4,
    banheiros: 6,
    vagas: 6,
    unidade: "21",
    torre: "A",
    andar: 2,
    matricula: "987654",
    titulo: "Apartamento Alto Padrão no Jardim Europa",
    descricao: "Vista deslumbrante, acabamento de altíssimo luxo.",
    endereco: {
      logradouro: "Rua Groenlândia",
      numero: "1500",
      complemento: "Apto 21",
      bairro: "Jardim Europa",
      cidade: "São Paulo",
      estado: "SP",
      cep: "01434-000",
      latitude: -23.5789,
      longitude: -46.6854,
    },
    fotos: [
      {
        url: "https://cdn.mbras.com.br/fotos/kenlo-ap8899-living.jpg",
        principal: true,
        ordem: 1,
        descricao: "Living amplo",
      },
      {
        url: "https://cdn.mbras.com.br/fotos/kenlo-ap8899-master.jpg",
        principal: false,
        ordem: 2,
        descricao: "Suíte master",
      },
    ],
    caracteristicas: ["Piscina", "Academia", "Varanda Gourmet"],
    exclusivo: true,
  };

  const result = KenloMapper.map(kenloPayload);

  // Unit assertions
  assert.equal(result.unit.property_type, "apartment");
  assert.equal(result.unit.usable_area_m2, 620);
  assert.equal(result.unit.bedrooms, 4);
  assert.equal(result.unit.suites, 4);
  assert.equal(result.unit.parking_spaces, 6);
  assert.equal(result.unit.matricula, "987654");
  assert.equal(result.unit.address?.street, "Rua Groenlândia");
  assert.equal(result.unit.address?.number, "1500");
  assert.equal(result.unit.address?.postal_code, "01434000");
  assert.equal(result.unit.condo_fee?.amount, 1450000); // R$ 14.500,00 -> 1.450.000 centavos
  assert.equal(result.unit.iptu_annual?.amount, 8000000); // R$ 80.000,00 -> 8.000.000 centavos
  assert.equal(result.unit.provenance.trust_tier, TRUST_TIERS.external_primary);

  // Property assertions
  assert.equal(result.property.code, "AP8899");
  assert.equal(result.property.transaction_type, "sale");
  assert.equal(result.property.property_status, "available");
  assert.equal(result.property.asking_price?.amount, 2200000000); // R$ 22.000.000,00 -> 2.200.000.000 centavos
  assert.equal(result.property.exclusive, true);
  assert.equal(result.property.external_ids[0]?.namespace, "kenlo");
  assert.equal(result.property.external_ids[0]?.value, "AP8899");

  // MediaAsset assertions
  assert.equal(result.media_assets.length, 2);
  assert.equal(result.media_assets[0]?.media_role, "cover");
  assert.equal(result.media_assets[0]?.is_cover, true);
  assert.equal(result.media_assets[1]?.media_role, "gallery");
});

test("ZapXMLMapper parses portal XML feeds and extracts canonical entities", () => {
  const rawXml = `
    <?xml version="1.0" encoding="UTF-8"?>
    <Carga>
      <Imoveis>
        <Imovel>
          <CodigoImovel>ZAP-5544</CodigoImovel>
          <TipoImovel>Cobertura</TipoImovel>
          <Finalidade>Venda</Finalidade>
          <Titulo>Cobertura Triplex Faria Lima</Titulo>
          <PrecoVenda>45000000</PrecoVenda>
          <ValorCondominio>25000</ValorCondominio>
          <AreaUtil>950</AreaUtil>
          <QtdDormitorios>5</QtdDormitorios>
          <QtdSuites>5</QtdSuites>
          <QtdVagas>8</QtdVagas>
          <Endereco>
            <Logradouro>Avenida Brigadeiro Faria Lima</Logradouro>
            <Numero>3500</Numero>
            <Bairro>Itaim Bibi</Bairro>
            <Cidade>São Paulo</Cidade>
            <Estado>SP</Estado>
            <CEP>04538-133</CEP>
          </Endereco>
          <Fotos>
            <Foto>https://imagens.zapimoveis.com.br/foto1.jpg</Foto>
            <Foto>https://imagens.zapimoveis.com.br/foto2.jpg</Foto>
          </Fotos>
          <Caracteristicas>
            <Item>Heliponto</Item>
            <Item>Piscina Privativa</Item>
          </Caracteristicas>
        </Imovel>
      </Imoveis>
    </Carga>
  `;

  const items = ZapXMLMapper.splitXmlItems(rawXml);
  assert.equal(items.length, 1);

  const mapped = ZapXMLMapper.mapXmlItem(items[0]!);
  assert.equal(mapped.property.code, "ZAP-5544");
  assert.equal(mapped.unit.property_type, "penthouse");
  assert.equal(mapped.property.asking_price?.amount, 4500000000);
  assert.equal(mapped.unit.usable_area_m2, 950);
  assert.equal(mapped.unit.bedrooms, 5);
  assert.equal(mapped.unit.parking_spaces, 8);
  assert.equal(mapped.unit.address?.street, "Avenida Brigadeiro Faria Lima");
  assert.equal(mapped.unit.address?.neighborhood_raw, "Itaim Bibi");
  assert.equal(mapped.media_assets.length, 2);
  assert.equal(mapped.unit.features.includes("Heliponto"), true);
});

test("ZapXMLMapper parses golden portal-feed.valid.xml correctly", () => {
  const goldenPath = join(process.cwd(), "tests/golden/portal-feed.valid.xml");
  const xmlContent = readFileSync(goldenPath, "utf-8");

  const items = ZapXMLMapper.splitXmlItems(xmlContent);
  assert.equal(items.length, 1);

  const mapped = ZapXMLMapper.mapXmlItem(items[0]!);
  assert.equal(mapped.property.code, "MB18495");
  assert.equal(mapped.property.headline, "Cobertura duplex no Itaim");
  assert.equal(mapped.unit.address?.neighborhood_raw, "Itaim Bibi");
});

test("PollingScheduler manages delta time windows, locking, and circuit breaker", () => {
  const job = PollingScheduler.createJob({
    source_id: "kenlo-source-uuid-1",
    source_system: "kenlo",
    poll_interval_seconds: 60,
    max_consecutive_failures: 3,
    base_backoff_seconds: 10,
    last_sync_timestamp: "2026-08-16T12:00:00.000Z",
  });

  assert.equal(job.status, "idle");
  assert.equal(job.consecutive_failures, 0);

  // 1. Acquire delta window
  const { job: runningJob, window } = PollingScheduler.acquireDeltaWindow(job);
  assert.ok(window !== null);
  assert.equal(runningJob.status, "running");
  assert.equal(window?.start_time, "2026-08-16T12:00:00.000Z");
  assert.ok(runningJob.current_lock_token !== null);

  // 2. Cannot acquire window when already running
  const { window: blockedWindow } = PollingScheduler.acquireDeltaWindow(runningJob);
  assert.equal(blockedWindow, null);

  // 3. Record success
  const successJob = PollingScheduler.recordSuccess(runningJob, window!, 15);
  assert.equal(successJob.status, "idle");
  assert.equal(successJob.current_lock_token, null);
  assert.equal(successJob.last_sync_timestamp, window!.end_time);

  // 4. Consecutive failures triggering circuit breaker
  const fail1 = PollingScheduler.recordFailure(successJob, new Error("API timeout 504"));
  assert.equal(fail1.consecutive_failures, 1);
  assert.equal(fail1.status, "idle");

  const fail2 = PollingScheduler.recordFailure(fail1, new Error("API timeout 504"));
  assert.equal(fail2.consecutive_failures, 2);
  assert.equal(fail2.status, "idle");

  const fail3 = PollingScheduler.recordFailure(fail2, new Error("API 500 Down"));
  assert.equal(fail3.consecutive_failures, 3);
  assert.equal(fail3.status, "circuit_broken");

  // 5. Circuit broken job cannot acquire delta window
  const { window: circuitBrokenWindow } = PollingScheduler.acquireDeltaWindow(fail3);
  assert.equal(circuitBrokenWindow, null);
});
