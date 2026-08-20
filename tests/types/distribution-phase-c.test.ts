import test from "node:test";
import assert from "node:assert/strict";
import {
  TwentyCRMSync,
  PortalXMLGenerator,
  FeedDispatcher,
  GenericCSVMapper,
} from "../../src/index.ts";
import type { ExposurePolicy } from "../../types/mbras.ts";

test("TwentyCRMSync converts canonical property and unit to TwentyCRM payload", () => {
  const { property, unit } = GenericCSVMapper.mapRow({
    rua: "Avenida Brigadeiro Faria Lima",
    numero: "3500",
    bairro: "Itaim Bibi",
    cidade: "São Paulo",
    uf: "SP",
    valor: 18000000,
    condominio: 15000,
    iptu: 60000,
    area_util: 520,
    dormitorios: 4,
    suites: 4,
    vagas: 6,
    titulo: "Edifício Infinity Faria Lima",
  });

  const mediaAssets = [
    {
      id: "media-uuid-1",
      scope: "property" as const,
      property_id: property.id,
      unit_id: unit.id,
      building_id: null,
      media_type: "photo" as const,
      media_role: "cover" as const,
      url: "https://cdn.mbras.com.br/infinity-1.jpg",
      storage_key: null,
      width: null,
      height: null,
      duration_s: null,
      order_index: 0,
      caption: null,
      media_rights: "owned" as const,
      visibility: "public" as const,
      is_cover: true,
      checksum: null,
      ai_tags: [],
      provenance: property.provenance,
      audit: property.audit,
    },
  ];

  const twentyPayload = TwentyCRMSync.toTwentyCRM({
    property,
    unit,
    media_assets: mediaAssets,
  });

  assert.equal(twentyPayload.name, "Edifício Infinity Faria Lima");
  assert.equal(twentyPayload.pibrasPropertyId, property.id);
  assert.equal(twentyPayload.pibrasUnitId, unit.id);
  assert.equal(twentyPayload.askingPriceAmount, 1800000000); // centavos
  assert.equal(twentyPayload.condoFeeAmount, 1500000);
  assert.equal(twentyPayload.usableAreaM2, 520);
  assert.equal(twentyPayload.bedrooms, 4);
  assert.equal(twentyPayload.neighborhood, "Itaim Bibi");
  assert.equal(twentyPayload.photos?.length, 1);
  assert.equal(twentyPayload.photos?.[0]?.url, "https://cdn.mbras.com.br/infinity-1.jpg");
});

test("TwentyCRMSync receives TwentyCRM update and applies authorized changes directly", () => {
  const { property, unit } = GenericCSVMapper.mapRow({
    rua: "Rua Groenlândia",
    numero: "1000",
    bairro: "Jardim Europa",
    valor: 20000000,
  });

  // TwentyCRM atualiza o preço de venda e o headline
  const updateResult = TwentyCRMSync.fromTwentyCRM({
    twentyPayload: {
      id: "twenty-prop-1",
      headline: "Mansão Atualizada pelo Corretor no CRM",
      askingPriceAmount: 1950000000,
      askingPriceCurrency: "BRL",
      status: "under_offer",
    },
    currentProperty: property,
    currentUnit: unit,
  });

  assert.equal(updateResult.propertyArbitration.action, "direct_apply");
  assert.equal(updateResult.propertyArbitration.applied_data["headline"], "Mansão Atualizada pelo Corretor no CRM");
  assert.equal(updateResult.propertyArbitration.applied_data["property_status"], "under_offer");
  assert.deepEqual(updateResult.propertyArbitration.applied_data["asking_price"], {
    amount: 1950000000,
    currency: "BRL",
  });
  assert.equal(updateResult.propertyArbitration.pending_change, null);
});

test("PortalXMLGenerator generates valid PIBRAS and ZAP feeds respecting ExposurePolicy", () => {
  const { property, unit } = GenericCSVMapper.mapRow({
    rua: "Rua Seridó",
    numero: "200",
    bairro: "Jardim Europa",
    cidade: "São Paulo",
    uf: "SP",
    valor: 35000000,
    area_util: 680,
    dormitorios: 4,
    titulo: "Exclusividade Seridó",
  });

  const publicPolicy: ExposurePolicy = {
    id: "00000000-0000-0000-0000-000000000050",
    tenant_id: null,
    resource_type: "property",
    resource_id: property.id,
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
    allowed_channels: ["portal", "website"],
    default_decision: "deny",
    audit_sensitive_reads: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const pibrasXml = PortalXMLGenerator.generatePibrasXml([
    {
      property,
      unit,
      policy: publicPolicy,
    },
  ]);

  assert.ok(pibrasXml.includes("<Listings>"));
  assert.ok(pibrasXml.includes("<Title>Exclusividade Seridó</Title>"));
  assert.ok(pibrasXml.includes("<Neighborhood>Jardim Europa</Neighborhood>"));
  assert.ok(pibrasXml.includes("<Price>35000000</Price>"));

  const zapXml = PortalXMLGenerator.generateZapXml([
    {
      property,
      unit,
      policy: publicPolicy,
    },
  ]);

  assert.ok(zapXml.includes("<Carga>"));
  assert.ok(zapXml.includes("<PrecoVenda>35000000</PrecoVenda>"));
  assert.ok(zapXml.includes("<Logradouro>Rua Seridó</Logradouro>"));
});

test("FeedDispatcher creates SharingEvent audit trail for LGPD compliance", () => {
  const { property, unit } = GenericCSVMapper.mapRow({
    rua: "Rua Leopoldo Couto de Magalhaes",
    numero: "1200",
    bairro: "Itaim Bibi",
    valor: 28000000,
  });

  const policy: ExposurePolicy = {
    id: "00000000-0000-0000-0000-000000000060",
    tenant_id: null,
    resource_type: "property",
    resource_id: property.id,
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

  const dispatchResult = FeedDispatcher.dispatch({
    tenant_id: "00000000-0000-0000-0000-000000000001",
    partner_relationship_id: "00000000-0000-0000-0000-000000000002",
    processing_purpose_id: "00000000-0000-0000-0000-000000000003",
    legal_basis_assessment_id: "00000000-0000-0000-0000-000000000004",
    field_allowlist_id: "00000000-0000-0000-0000-000000000005",
    field_allowlist_version: 1,
    allowed_fields: ["code", "headline", "asking_price", "address.neighborhood_raw", "usable_area_m2"],
    channel_type: "portal",
    items: [{ property, unit, policy }],
  });

  assert.equal(dispatchResult.record_count, 1);
  assert.equal(dispatchResult.channel_type, "portal");
  assert.ok(dispatchResult.payload.includes("<Listings>"));
  assert.equal(dispatchResult.sharing_event.status, "delivered");
  assert.ok(dispatchResult.sharing_event.payload_digest.length === 64);
  assert.equal(dispatchResult.sharing_event.shared_fields.length, 5);
});
