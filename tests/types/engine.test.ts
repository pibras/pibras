import test from "node:test";
import assert from "node:assert/strict";
import {
  RawReceiver,
  GenericCSVMapper,
  parseBRLToCentavos,
  normalizeStreetName,
  normalizeNeighborhood,
  buildNormalizedAddressKey,
  UnitMatcher,
  SurvivorshipArbitrator,
  ExposurePolicyEvaluator,
  MediaUploader,
  MediaProcessor,
  computeAverageHash,
  hammingDistance,
  isVisualMatch,
  findBestVisualMatch,
  buildStorageKey,
  mimeToExtension,
  detectMediaType,
  OPERATOR_BRAND,
} from "../../src/index.ts";
import type { ExposurePolicy } from "../../types/mbras.ts";
import { TRUST_TIERS } from "../../types/mbras.ts";

test("RawReceiver computes deterministic hash and attaches provenance", () => {
  const payload = {
    titulo: "Cobertura Itaim",
    valor: 25000000,
    bairro: "Itaim Bibi",
  };

  const receipt = RawReceiver.receive({
    source_system: "kenlo",
    payload,
    source_record_id: "KENLO-9988",
  });

  assert.equal(receipt.source_system, "kenlo");
  assert.equal(receipt.trust_tier, TRUST_TIERS.external_primary);
  assert.equal(receipt.provenance.source_record_id, "KENLO-9988");
  assert.ok(receipt.payload_sha256.length === 64, "SHA-256 hash must be 64 hex chars");
  assert.ok(receipt.provenance.raw_payload_ref?.startsWith("ingestion://"));
});

test("GenericCSVMapper converts Brazilian currency string to integer centavos", () => {
  const money = parseBRLToCentavos("R$ 18.500.000,00");
  assert.deepEqual(money, {
    amount: 1850000000,
    currency: "BRL",
  });

  const moneyFromInt = parseBRLToCentavos(12000000);
  assert.deepEqual(moneyFromInt, {
    amount: 1200000000,
    currency: "BRL",
  });
});

test("Normalizer handles Brazilian address abbreviations and neighborhood aliases", () => {
  assert.equal(normalizeStreetName("R. Leopoldo Couto de Magalhães Jr"), "rua leopoldo couto de magalhaes jr");
  assert.equal(normalizeStreetName("Av. Brigadeiro Faria Lima"), "avenida brigadeiro faria lima");
  assert.equal(normalizeStreetName("Al. Gabriel Monteiro da Silva"), "alameda gabriel monteiro da silva");

  assert.equal(normalizeNeighborhood("Jd. Europa"), "jardim europa");
  assert.equal(normalizeNeighborhood("V. Nova Conceição"), "vila nova conceicao");
  assert.equal(normalizeNeighborhood("Itaim"), "itaim bibi");

  const addrKey = buildNormalizedAddressKey({
    street: "R. Leopoldo Couto",
    number: "1200",
    neighborhood_raw: "Jd. Europa",
    city: "São Paulo",
    state: "SP",
    country: "BR",
  });

  assert.equal(addrKey, "br:sp:sao_paulo:jardim_europa:rua_leopoldo_couto:1200");
});

test("UnitMatcher accurately deduplicates properties by matricula and address", () => {
  const candidate = GenericCSVMapper.mapRow({
    rua: "Rua Leopoldo Couto de Magalhaes",
    numero: "1200",
    bairro: "Itaim Bibi",
    unidade: "141",
    area_util: "450",
    dormitorios: "4",
    vagas: "5",
    matricula: "123.456",
  }).unit;

  const existingInventory = [
    {
      id: "unit-uuid-1",
      matricula: "123456",
      normalized_address_key: "br:sp:sao_paulo:itaim_bibi:rua_leopoldo_couto_de_magalhaes:1200",
      usable_area_m2: 450,
      unit_number: "141",
    },
    {
      id: "unit-uuid-2",
      matricula: "999999",
      normalized_address_key: "br:sp:sao_paulo:jardim_europa:rua_europa:500",
      usable_area_m2: 300,
    },
  ];

  const match = UnitMatcher.match(candidate, existingInventory);
  assert.equal(match.candidate_unit_id, "unit-uuid-1");
  assert.equal(match.confidence, 1.0);
  assert.equal(match.review_state, "auto_matched");
});

test("SurvivorshipArbitrator protects proprietary data and creates PendingChange for untrusted sources", () => {
  const existingProp = {
    headline: "Mansão Jardim Europa",
    asking_price: { amount: 3500000000, currency: "BRL" },
    exclusive: true,
  };

  // 1. Atualização externa (Kenlo: tier 4) tentando alterar preço de dado aprovado internamente (tier 2)
  const result = SurvivorshipArbitrator.arbitrate({
    entity_type: "property",
    entity_id: "prop-uuid-1",
    current_data: existingProp,
    current_trust_tier: TRUST_TIERS.mbras_internal,
    incoming_data: {
      asking_price: { amount: 3200000000, currency: "BRL" },
    },
    incoming_source: "kenlo",
    incoming_trust_tier: TRUST_TIERS.external_primary,
  });

  assert.equal(result.action, "create_pending_change");
  assert.ok(result.pending_change !== null);
  assert.equal(result.pending_change?.state, "pending_review");
  // O dado proprietário continua intacto:
  assert.deepEqual(result.applied_data["asking_price"], { amount: 3500000000, currency: "BRL" });

  // 2. Atualização vinda da Diretoria (tier 1): aceita diretamente
  const directResult = SurvivorshipArbitrator.arbitrate({
    entity_type: "property",
    entity_id: "prop-uuid-1",
    current_data: existingProp,
    current_trust_tier: TRUST_TIERS.mbras_internal,
    incoming_data: {
      asking_price: { amount: 3400000000, currency: "BRL" },
    },
    incoming_source: "mbras_internal",
    incoming_trust_tier: TRUST_TIERS.diretoria_approved,
  });

  assert.equal(directResult.action, "direct_apply");
  assert.equal(directResult.pending_change, null);
  assert.deepEqual(directResult.applied_data["asking_price"], { amount: 3400000000, currency: "BRL" });
});

test("ExposurePolicyEvaluator enforces default-deny and masks sensitive fields for public channels", () => {
  const policy: ExposurePolicy = {
    id: "00000000-0000-0000-0000-000000000001",
    tenant_id: null,
    resource_type: "property",
    resource_id: "00000000-0000-0000-0000-000000000002",
    exposure_level: "confidential",
    rules: [
      {
        priority: 10,
        effect: "allow",
        actions: ["publish", "read"],
        fields: [],
        roles: ["website_visitor", "public_website"],
        conditions: {},
        reason_code: null,
      },
    ],
    requires_approval_for: [],
    allowed_channels: ["website", "crm"],
    default_decision: "deny",
    audit_sensitive_reads: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const { property, unit } = GenericCSVMapper.mapRow({
    rua: "Rua Seridó",
    numero: "100",
    complemento: "Apto 201",
    bairro: "Jardim Europa",
    cidade: "São Paulo",
    valor: 40000000,
  });

  // Projeção para site público com nível confidencial
  // Requires approval_record since the approval gate was added in Phase A (G5)
  const projection = ExposurePolicyEvaluator.projectForChannel({
    property,
    unit,
    policy,
    context: {
      action: "publish",
      channel_type: "website",
      caller_role: "public_website",
    },
    approval_record: {
      approved_by: "director-uuid-1",
      approved_at: new Date().toISOString(),
      approval_scope: "website_publication",
    },
  });

  assert.ok(projection !== null);
  assert.equal(projection?.evaluation.decision, "mask");
  // O número do endereço e complemento foram mascarados
  assert.equal(projection?.unit?.address?.number, null);
  assert.equal(projection?.unit?.address?.complement, null);
  assert.equal(projection?.unit?.address?.street, null);
  // O preço foi mascarado
  assert.equal(projection?.property.asking_price, undefined);
});

// ====================================================================
// Phase A: Field Authority Matrix + Approval Gate tests
// ====================================================================

import {
  resolveFieldAuthority,
  isAuthorized,
  DEFAULT_AUTHORITY_MATRIX,
} from "../../src/survivorship/field-authority.ts";
import type { FieldAuthorityRule } from "../../src/survivorship/field-authority.ts";

test("FieldAuthority resolves exact entity+field match before wildcard", () => {
  const rule = resolveFieldAuthority(DEFAULT_AUTHORITY_MATRIX, "property", "asking_price");
  assert.ok(rule !== undefined);
  assert.equal(rule?.fallback_action, "manual_approval");
  assert.ok(rule?.authority_systems.includes("twenty_crm"));
  assert.ok(rule?.authority_systems.includes("mbras_internal"));
});

test("FieldAuthority resolves wildcard entity for address fields", () => {
  const rule = resolveFieldAuthority(DEFAULT_AUTHORITY_MATRIX, "building", "address");
  assert.ok(rule !== undefined);
  assert.equal(rule?.entity_type, "*");
  assert.equal(rule?.fallback_action, "pending_change");
});

test("FieldAuthority returns undefined for unprotected fields", () => {
  const rule = resolveFieldAuthority(DEFAULT_AUTHORITY_MATRIX, "property", "some_random_field");
  assert.equal(rule, undefined);
});

test("FieldAuthority isAuthorized checks source against authority list", () => {
  const rule = resolveFieldAuthority(DEFAULT_AUTHORITY_MATRIX, "property", "asking_price")!;
  assert.equal(isAuthorized(rule, "mbras_internal"), true);
  assert.equal(isAuthorized(rule, "twenty_crm"), true);
  assert.equal(isAuthorized(rule, "kenlo"), false);
  assert.equal(isAuthorized(rule, "csv_import"), false);
});

test("FieldAuthority never_overwrite blocks PII fields entirely", () => {
  const rule = resolveFieldAuthority(DEFAULT_AUTHORITY_MATRIX, "party", "tax_id");
  assert.ok(rule !== undefined);
  assert.equal(rule?.fallback_action, "never_overwrite");
  assert.equal(isAuthorized(rule!, "kenlo"), false);
  assert.equal(isAuthorized(rule!, "mbras_internal"), true);
});

test("SurvivorshipArbitrator mixed result: headline applied, asking_price to PendingChange", () => {
  const result = SurvivorshipArbitrator.arbitrate({
    entity_type: "property",
    entity_id: "prop-uuid-mixed",
    current_data: {
      headline: "Old headline",
      asking_price: { amount: 3500000000, currency: "BRL" },
    },
    current_trust_tier: TRUST_TIERS.mbras_internal,
    incoming_data: {
      headline: "Updated headline from Kenlo",
      asking_price: { amount: 3200000000, currency: "BRL" },
    },
    incoming_source: "kenlo",
    incoming_trust_tier: TRUST_TIERS.external_primary,
  });

  // Mixed result: headline applied directly, asking_price routed to PendingChange
  assert.equal(result.action, "mixed");
  assert.equal(result.applied_data["headline"], "Updated headline from Kenlo");
  // asking_price remains unchanged in applied_data
  assert.deepEqual(result.applied_data["asking_price"], { amount: 3500000000, currency: "BRL" });
  // PendingChange contains the asking_price update
  assert.ok(result.pending_change !== null);
  assert.deepEqual(result.pending_change?.proposed["asking_price"], { amount: 3200000000, currency: "BRL" });
  assert.equal(result.pending_change?.proposed["headline"], undefined);
});

test("ApprovalGate denies confidential property on portal without approval_record", () => {
  const policy: ExposurePolicy = {
    id: "00000000-0000-0000-0000-000000000010",
    tenant_id: null,
    resource_type: "property",
    resource_id: "00000000-0000-0000-0000-000000000011",
    exposure_level: "confidential",
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
    allowed_channels: ["portal", "crm"],
    default_decision: "deny",
    audit_sensitive_reads: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const { property, unit } = GenericCSVMapper.mapRow({
    rua: "Rua Seridó",
    numero: "100",
    bairro: "Jardim Europa",
    valor: 40000000,
  });

  // No approval_record → must be denied
  const projection = ExposurePolicyEvaluator.projectForChannel({
    property,
    unit,
    policy,
    context: {
      action: "publish",
      channel_type: "portal",
      caller_role: "portal_feed",
    },
    // approval_record not provided
  });

  assert.ok(projection !== null);
  assert.equal(projection?.evaluation.decision, "deny");
  assert.ok(projection?.evaluation.reasons[0]?.includes("Ultra-luxury gate"));
});

test("ApprovalGate allows confidential property on portal WITH valid approval_record", () => {
  const policy: ExposurePolicy = {
    id: "00000000-0000-0000-0000-000000000012",
    tenant_id: null,
    resource_type: "property",
    resource_id: "00000000-0000-0000-0000-000000000013",
    exposure_level: "confidential",
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
    allowed_channels: ["portal", "crm"],
    default_decision: "deny",
    audit_sensitive_reads: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const { property, unit } = GenericCSVMapper.mapRow({
    rua: "Rua Seridó",
    numero: "100",
    bairro: "Jardim Europa",
    valor: 40000000,
  });

  // WITH valid approval_record → should pass the gate (but still apply masking)
  const projection = ExposurePolicyEvaluator.projectForChannel({
    property,
    unit,
    policy,
    context: {
      action: "publish",
      channel_type: "portal",
      caller_role: "portal_feed",
    },
    approval_record: {
      approved_by: "director-uuid-1",
      approved_at: new Date().toISOString(),
      approval_scope: "portal_publication",
    },
  });

  assert.ok(projection !== null);
  // Should pass the gate but still get masking (confidential on portal)
  assert.notEqual(projection?.evaluation.decision, "deny");
});

test("ApprovalGate does NOT block confidential property on CRM channel", () => {
  const policy: ExposurePolicy = {
    id: "00000000-0000-0000-0000-000000000014",
    tenant_id: null,
    resource_type: "property",
    resource_id: "00000000-0000-0000-0000-000000000015",
    exposure_level: "confidential",
    rules: [
      {
        priority: 10,
        effect: "allow",
        actions: ["read"],
        fields: [],
        roles: ["internal_broker"],
        conditions: {},
        reason_code: null,
      },
    ],
    requires_approval_for: [],
    allowed_channels: ["crm", "portal"],
    default_decision: "deny",
    audit_sensitive_reads: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const { property, unit } = GenericCSVMapper.mapRow({
    rua: "Rua Seridó",
    numero: "100",
    bairro: "Jardim Europa",
    valor: 40000000,
  });

  // CRM channel should NOT trigger the approval gate (only portal/website/paid_ad)
  const projection = ExposurePolicyEvaluator.projectForChannel({
    property,
    unit,
    policy,
    context: {
      action: "read",
      channel_type: "crm",
      caller_role: "internal_broker",
    },
    // No approval_record — but CRM doesn't need one
  });

  assert.ok(projection !== null);
  // Should NOT be denied by the approval gate
  assert.notEqual(projection?.evaluation.decision, "deny");
});

// ================================================================
// Phase C: Media Pipeline & Visual Deduplication
// ================================================================

test("MediaUploader processes upload with SHA-256 checksum and deterministic storage key", () => {
  const fakeBuffer = Buffer.from("fake-jpeg-content-for-testing-upload-pipeline");
  const provenance = {
    source_system: "mbras_internal" as const,
    source_record_id: null,
    source_url: null,
    trust_tier: 1 as const,
    ingested_at: new Date().toISOString(),
    ingested_by: "test",
    sync_batch_id: null,
    raw_payload_ref: null,
  };

  const result = MediaUploader.processUpload({
    file_buffer: fakeBuffer,
    original_filename: "IMG_2045.jpg",
    content_type: "image/jpeg",
    scope: "property",
    entity_id: "prop-uuid-1",
    media_role: "cover",
    provenance,
  });

  assert.ok(result.checksum_sha256.length === 64, "SHA-256 must be 64 hex chars");
  assert.ok(result.storage_key.startsWith("property/prop-uuid-1/"));
  assert.ok(result.storage_key.endsWith(".jpg"));
  assert.equal(result.media_asset.media_type, "photo");
  assert.equal(result.media_asset.media_role, "cover");
  assert.equal(result.media_asset.is_cover, true);
  assert.equal(result.media_asset.scope, "property");
  assert.equal(result.size_bytes, fakeBuffer.length);
});

test("MediaUploader findExactDuplicate detects identical checksum", () => {
  const checksum = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"; // pragma: allowlist secret
  const existing = [
    { id: "asset-1", checksum: "0000000000000000000000000000000000000000000000000000000000000000" },
    { id: "asset-2", checksum },
    { id: "asset-3", checksum: null },
  ];

  const dup = MediaUploader.findExactDuplicate(checksum, existing);
  assert.equal(dup, "asset-2");

  const noDup = MediaUploader.findExactDuplicate("ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", existing);
  assert.equal(noDup, null);
});

test("MediaProcessor creates complete image pipeline with thumbnail, gallery, full, pHash, and metadata", () => {
  const jobs = MediaProcessor.createImagePipeline({
    media_asset_id: "asset-uuid-1",
    storage_key: "property/prop-1/abc123.jpg",
  });

  assert.equal(jobs.length, 5);

  const jobTypes = jobs.map((j) => j.job_type);
  assert.ok(jobTypes.includes("resize"), "Must include resize jobs");
  assert.ok(jobTypes.includes("convert_webp"), "Must include WebP conversion");
  assert.ok(jobTypes.includes("phash"), "Must include pHash computation");
  assert.ok(jobTypes.includes("extract_metadata"), "Must include metadata extraction");

  // All jobs start in pending state
  for (const job of jobs) {
    assert.equal(job.status, "pending");
    assert.equal(job.attempts, 0);
    assert.equal(job.max_attempts, 3);
  }

  // Test success recording
  const completed = MediaProcessor.recordSuccess(jobs[0]!, {
    output_storage_key: "property/prop-1/abc123_thumb.webp",
    output_url: "https://media.mbras.com.br/property/prop-1/abc123_thumb.webp",
    width: 400,
    height: 300,
    size_bytes: 15000,
  });
  assert.equal(completed.status, "completed");
  assert.ok(completed.completed_at !== null);

  // Test failure recording with max_attempts exhaustion
  let failedJob = jobs[1]!;
  for (let i = 0; i < 3; i++) {
    failedJob = MediaProcessor.recordFailure(failedJob, "sharp: ENOMEM");
  }
  assert.equal(failedJob.status, "failed");
  assert.equal(failedJob.attempts, 3);
});

test("MediaProcessor watermark profiles respect channel configuration", () => {
  const portalJob = MediaProcessor.createWatermarkJob({
    media_asset_id: "asset-1",
    storage_key: "property/prop-1/img.jpg",
    channel: "portal",
  });
  assert.ok(portalJob !== null);
  assert.equal(portalJob!.params.watermark_text, OPERATOR_BRAND);
  assert.equal(portalJob!.params.watermark_opacity, 0.35);

  const offMarketJob = MediaProcessor.createWatermarkJob({
    media_asset_id: "asset-1",
    storage_key: "property/prop-1/img.jpg",
    channel: "off_market_pdf",
  });
  assert.ok(offMarketJob !== null);
  assert.equal(offMarketJob!.params.watermark_text, `CONFIDENCIAL \u2022 ${OPERATOR_BRAND}`);
  assert.equal(offMarketJob!.params.watermark_position, "tiled");

  // CRM channel has no watermark
  const crmJob = MediaProcessor.createWatermarkJob({
    media_asset_id: "asset-1",
    storage_key: "property/prop-1/img.jpg",
    channel: "crm",
  });
  assert.equal(crmJob, null);
});

test("pHash: computeAverageHash and hammingDistance work correctly", () => {
  // Two identical 8x8 luminance arrays should produce identical hashes
  const lum1 = Array.from({ length: 64 }, (_, i) => (i < 32 ? 200 : 50));
  const lum2 = [...lum1];
  const hash1 = computeAverageHash(lum1);
  const hash2 = computeAverageHash(lum2);
  assert.equal(hash1, hash2);
  assert.equal(hammingDistance(hash1, hash2), 0);
  assert.equal(isVisualMatch(hash1, hash2), true);

  // Slightly different arrays (2 pixels changed) should still be a visual match
  const lum3 = [...lum1];
  lum3[30] = 50; // Flip one pixel from bright to dark
  lum3[33] = 200; // Flip one pixel from dark to bright
  const hash3 = computeAverageHash(lum3);
  assert.ok(hammingDistance(hash1, hash3) <= 8, "2 pixel changes should be within threshold");

  // Completely different arrays should NOT match
  const lumInverse = lum1.map((v) => 255 - v);
  const hashInverse = computeAverageHash(lumInverse);
  assert.ok(hammingDistance(hash1, hashInverse) > 8, "Inverse should NOT match");
  assert.equal(isVisualMatch(hash1, hashInverse), false);

  // findBestVisualMatch across sets
  const matchResult = findBestVisualMatch([hash1], [hash3, hashInverse]);
  assert.ok(matchResult !== null);
  assert.equal(matchResult!.is_match, true);
  assert.equal(matchResult!.hash_b, hash3);
});

test("UnitMatcher scores IPTU, condomínio, and pHash visual signals", () => {
  // Create a luminance hash for testing
  const lumPattern = Array.from({ length: 64 }, (_, i) => (i % 3 === 0 ? 180 : 60));
  const testHash = computeAverageHash(lumPattern);

  const { property, unit } = GenericCSVMapper.mapRow({
    rua: "Rua Seridó",
    numero: "100",
    complemento: "Apto 201",
    bairro: "Jardim Europa",
    cidade: "São Paulo",
    valor: 32000000,
  });

  // Set IPTU and condo fee on the incoming unit
  const incomingUnit = {
    ...unit,
    iptu_annual: { amount: 1200000, currency: "BRL" as const },
    condo_fee: { amount: 350000, currency: "BRL" as const },
  };

  const existing = [
    {
      id: "existing-1",
      normalized_address_key: unit.normalized_address_key,
      unit_number: "201",
      usable_area_m2: unit.usable_area_m2,
      bedrooms: unit.bedrooms,
      parking_spaces: unit.parking_spaces,
      iptu_annual_amount: 1210000,  // Within 5% of 1200000
      condo_fee_amount: 345000,     // Within 5% of 350000
      media_checksums: [testHash],  // Visual match
    },
  ];

  // Cast incoming to carry media_checksums for the matcher
  const incomingWithHashes = Object.assign(incomingUnit, {
    media_checksums: [testHash],
  });

  const result = UnitMatcher.match(incomingWithHashes, existing);

  // Score: address(0.50) + IPTU(0.05) + condo(0.05) + pHash(0.10) = 0.70
  // No unit_number match because GenericCSVMapper maps "complemento" to address.complement, not unit_number
  assert.ok(result.confidence >= 0.65, `Expected >= 0.65 confidence, got ${result.confidence}`);
  assert.equal(result.review_state, "needs_review");
  assert.ok(result.match_reasons.some((r) => r.includes("IPTU")), "Should include IPTU signal");
  assert.ok(result.match_reasons.some((r) => r.includes("Condo fee")), "Should include Condo fee signal");
  assert.ok(result.match_reasons.some((r) => r.includes("pHash")), "Should include pHash signal");
});
