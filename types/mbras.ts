/**
 * Padrão PIBRAS de Dados Imobiliários — Modelo Canônico
 * Schemas Zod + tipos TypeScript inferidos. Versão 0.1.0 (2026-06-18).
 *
 * Fonte de verdade: docs/PROPERTY-STANDARD-v0.1.md
 * Mantenha em paralelo com schema/mbras.schema.json e db/schema.sql.
 *
 *   npm i zod
 *
 * Convenções: dinheiro em centavos (inteiro); instantes ISO 8601 UTC; áreas em m²; coords WGS84.
 */

import { z } from "zod";

/* ------------------------------------------------------------------ *
 * Enums canônicos
 * ------------------------------------------------------------------ */

export const SourceSystem = z.enum([
  "mbras_internal", "twenty_crm", "kenlo", "vista", "jetimob", "imobzi",
  "tecimob", "orulo", "zap_vivareal", "olx", "xml_generic", "csv_import",
  "excel_import", "manual", "other",
]);

export const RecordState = z.enum([
  "draft", "pending_review", "active", "conflict", "duplicate", "rejected", "archived",
]);

export const PropertyType = z.enum([
  "apartment", "penthouse", "house", "house_condo", "studio", "loft", "flat",
  "land", "farm", "commercial_room", "commercial_building", "warehouse",
  "hotel", "whole_building", "other",
]);

export const TransactionType = z.enum(["sale", "rent", "sale_rent", "season_rent"]);

export const PropertyStatus = z.enum([
  "draft", "available", "reserved", "under_offer", "sold", "rented",
  "suspended", "off_market", "archived",
]);

export const Availability = z.enum(["available", "unavailable", "conditioned"]);
export const Currency = z.enum(["BRL", "USD", "EUR"]);
export const ExposureLevel = z.enum(["public", "restricted", "confidential", "off_market"]);
export const Confidentiality = z.enum(["normal", "sensitive", "highly_confidential"]);
export const MediaType = z.enum(["photo", "video", "floor_plan", "virtual_tour", "document", "aerial"]);
export const MediaRole = z.enum(["cover", "gallery", "floor_plan", "facade", "common_area", "view", "amenity", "other"]);
export const MediaRights = z.enum(["owned", "licensed", "restricted"]);
export const ChannelType = z.enum(["website", "portal", "crm", "broker_network", "off_market_pdf", "paid_ad", "landing_page", "whatsapp", "email"]);
export const OwnerType = z.enum(["individual", "company"]);
export const OwnerRole = z.enum(["owner", "representative", "heir", "attorney"]);
export const BrokerRole = z.enum(["listing", "co_listing", "capture"]);
export const DocumentType = z.enum(["matricula", "iptu", "contrato", "escritura", "laudo_avaliacao", "planta_aprovada", "habite_se", "other"]);
export const ListingStatus = z.enum(["draft", "published", "paused", "expired", "removed"]);
export const PriceDisplay = z.enum(["visible", "on_request"]);
export const AddressDisplay = z.enum(["full", "approximate", "hidden"]);
export const SunOrientation = z.enum(["morning", "afternoon", "full_day", "none"]);
export const BuildingStatus = z.enum(["planning", "under_construction", "ready"]);
export const GeoPrecision = z.enum(["exact", "approximate", "neighborhood", "none"]);
export const ComputedBy = z.enum(["human", "agent", "hermes"]);
export const GeographyType = z.enum(["country", "state", "city", "zone", "neighborhood", "microregion", "condominium_region"]);
export const PartyType = z.enum(["individual", "company"]);
export const PolicyEffect = z.enum(["allow", "deny"]);
export const PolicyAction = z.enum(["read", "write", "publish", "export", "send", "approve"]);
export const PolicyDecision = z.enum(["allow", "deny", "mask", "needs_approval"]);
export const PolicyResourceType = z.enum(["unit", "property", "listing", "media", "document", "party", "price", "address"]);
export const DedupeReviewState = z.enum(["unreviewed", "auto_matched", "needs_review", "confirmed_duplicate", "confirmed_unique"]);
export const RetentionAction = z.enum(["delete", "anonymize", "review", "archive"]);
export const DataSubjectRequestType = z.enum(["access", "correction", "deletion", "portability", "objection"]);
export const DataSubjectRequestStatus = z.enum(["received", "verifying_identity", "in_progress", "fulfilled", "rejected", "expired"]);
export const ImportSourceType = z.enum(["api", "csv", "excel", "xml", "database_dump", "manual"]);
export const ImportBatchStatus = z.enum(["draft", "mapping", "validating", "reviewing", "imported", "failed", "cancelled"]);
export const AuditChangeType = z.enum(["insert", "update", "delete"]);
export const LegalBasisType = z.enum(["consent", "legal_obligation", "public_policy", "research", "contract", "judicial_exercise", "life_protection", "health_protection", "legitimate_interest", "credit_protection"]);
export const AssessmentStatus = z.enum(["draft", "approved", "rejected", "expired"]);
export const PartnerRole = z.enum(["operator", "independent_controller", "joint_controller"]);
export const AllowlistStatus = z.enum(["draft", "active", "suspended", "retired"]);
export const SharingEventStatus = z.enum(["authorized", "delivered", "failed", "blocked"]);
export const DSARPropagationStatus = z.enum(["pending", "sent", "acknowledged", "fulfilled", "failed"]);
export const AutomatedDecisionOutcome = z.enum(["approved", "denied", "routed", "flagged", "no_effect"]);
export const AutomatedReviewStatus = z.enum(["not_requested", "requested", "under_review", "completed"]);
export const LegacyQualificationStatus = z.enum(["draft", "reviewing", "approved", "rejected", "quarantined", "imported"]);

/** Hierarquia de confiança para resolução de conflito (menor = mais confiável). */
export const TrustTier = z.number().int().min(1).max(6);
export const TRUST_TIERS = {
  diretoria_approved: 1,
  mbras_internal: 2,
  twenty_crm: 3,
  external_primary: 4,
  xml_feed: 5,
  spreadsheet_import: 6,
} as const;

/* ------------------------------------------------------------------ *
 * Tipos compartilhados
 * ------------------------------------------------------------------ */

const uuid = z.string().uuid();
const datetime = z.string().datetime({ offset: true });
const dateOnly = z.string().date();

/** Dinheiro: amount em centavos. Ex.: R$ 17.500.000,00 -> { amount: 1750000000, currency: "BRL" } */
export const Money = z.object({
  amount: z.number().int(),
  currency: Currency,
}).strict();

export const ExternalId = z.object({
  namespace: z.string(),
  key: z.string(),
  value: z.string(),
}).strict();

export const Provenance = z.object({
  source_system: SourceSystem,
  source_record_id: z.string().nullish(),
  source_url: z.string().url().nullish(),
  trust_tier: TrustTier,
  ingested_at: datetime,
  ingested_by: z.string().nullish(),
  sync_batch_id: uuid.nullish(),
  raw_payload_ref: z.string().nullish(),
}).strict();

export const DataQuality = z.object({
  missing_fields: z.array(z.string()).default([]),
  warnings: z.array(z.string()).default([]),
}).strict();

export const AuditStamp = z.object({
  created_at: datetime,
  updated_at: datetime,
  created_by: z.string().nullish(),
  updated_by: z.string().nullish(),
  version: z.number().int().min(1),
  record_state: RecordState,
  completeness_score: z.number().int().min(0).max(100).nullish(),
  data_quality: DataQuality.optional(),
}).strict();

export const Address = z.object({
  street: z.string().nullish(),
  number: z.string().nullish(), // mascarável conforme ExposureRule
  complement: z.string().nullish(),
  neighborhood_id: uuid.nullish(),
  neighborhood_raw: z.string().nullish(),
  city: z.string().nullish(),
  state: z.string().length(2).nullish(), // UF
  postal_code: z.string().nullish(), // CEP
  country: z.string().length(2).default("BR"),
  latitude: z.number().min(-90).max(90).nullish(),
  longitude: z.number().min(-180).max(180).nullish(),
  geo_precision: GeoPrecision.optional(),
  formatted: z.string().nullish(),
}).strict();

/* ------------------------------------------------------------------ *
 * Entidades
 * ------------------------------------------------------------------ */

export const Organization = z.object({
  id: uuid,
  name: z.string(),
  legal_name: z.string().nullish(),
  tax_id: z.string().nullish(),
  website_url: z.string().url().nullish(),
  country: z.string().length(2),
  created_at: datetime,
  updated_at: datetime,
}).strict();

export const Tenant = z.object({
  id: uuid,
  organization_id: uuid,
  name: z.string(),
  data_controller_tenant_id: uuid.nullish(),
  data_processor_org_id: uuid.nullish(),
  retention_policy_id: uuid.nullish(),
  international_transfer_allowed: z.boolean().default(false),
  active: z.boolean(),
  created_at: datetime,
  updated_at: datetime,
}).strict();

export const User = z.object({
  id: uuid,
  tenant_id: uuid.nullish(),
  organization_id: uuid.nullish(),
  name: z.string(),
  email: z.string().email().nullish(),
  roles: z.array(z.string()),
  active: z.boolean(),
  created_at: datetime,
  updated_at: datetime,
}).strict();

export const Building = z.object({
  id: uuid,
  name: z.string(),
  developer: z.string().nullish(),
  address: Address,
  building_status: BuildingStatus.optional(),
  year_built: z.number().int().nullish(),
  delivery_date: dateOnly.nullish(),
  floors: z.number().int().nullish(),
  towers: z.number().int().nullish(),
  total_units: z.number().int().nullish(),
  amenities: z.array(z.string()).default([]),
  description: z.string().nullish(),
  provenance: Provenance,
  audit: AuditStamp,
}).strict();

export const Unit = z.object({
  id: uuid,
  building_id: uuid.nullish(),
  matricula: z.string().nullish(), // chave durável de identidade física
  dedupe_key: z.string().nullish(),
  normalized_address_key: z.string().nullish(),
  area_signature: z.string().nullish(),
  duplicate_of_unit_id: uuid.nullish(),
  dedupe_confidence: z.number().min(0).max(1).nullish(),
  dedupe_review_state: DedupeReviewState.default("unreviewed"),
  property_type: PropertyType,
  address: Address.optional(),
  unit_number: z.string().nullish(),
  tower: z.string().nullish(),
  floor: z.number().int().nullish(),
  usable_area_m2: z.number().min(0).nullish(),
  total_area_m2: z.number().min(0).nullish(),
  lot_area_m2: z.number().min(0).nullish(),
  bedrooms: z.number().int().min(0).nullish(),
  suites: z.number().int().min(0).nullish(),
  bathrooms: z.number().int().min(0).nullish(),
  parking_spaces: z.number().int().min(0).nullish(),
  sun_orientation: SunOrientation.optional(),
  view_type: z.string().nullish(),
  ceiling_height_m: z.number().min(0).nullish(),
  features: z.array(z.string()).default([]),
  condo_fee: Money.optional(),
  iptu_annual: Money.optional(),
  provenance: Provenance,
  audit: AuditStamp,
}).strict();

export const PropertyOwnerLink = z.object({
  owner_id: uuid,
  ownership_pct: z.number().min(0).max(100).nullish(),
  owner_role: OwnerRole.default("owner"),
  is_primary: z.boolean().default(false),
}).strict();

export const PropertyBrokerLink = z.object({
  broker_id: uuid,
  broker_role: BrokerRole.default("listing"),
  is_primary: z.boolean().default(false),
  assigned_at: datetime.nullish(),
}).strict();

export const PropertyIntelligence = z.object({
  property_id: uuid.nullish(),
  ideal_buyer_profile: z.string().nullish(),
  likely_objections: z.array(z.string()).default([]),
  selling_arguments: z.array(z.string()).default([]),
  privacy_level: z.string().nullish(),
  rarity_score: z.number().int().min(0).max(100).nullish(),
  architecture_notes: z.string().nullish(),
  view_quality: z.number().int().min(0).max(100).nullish(),
  natural_light: z.number().int().min(0).max(100).nullish(),
  noise_level: z.number().int().min(0).max(100).nullish(),
  liquidity_score: z.number().int().min(0).max(100).nullish(),
  match_score: z.number().int().min(0).max(100).nullish(),
  defensible_price: Money.optional(),
  off_market_potential: z.number().int().min(0).max(100).nullish(),
  demand_notes: z.string().nullish(),
  last_computed_at: datetime.nullish(),
  computed_by: ComputedBy.optional(),
  confidence: z.number().int().min(0).max(100).nullish(),
}).strict();

export const Property = z.object({
  id: uuid,
  code: z.string().nullish(),
  external_ids: z.array(ExternalId).default([]),
  unit_id: uuid,
  building_id: uuid.nullish(),
  transaction_type: TransactionType,
  property_status: PropertyStatus.default("draft"),
  availability: Availability.optional(),
  asking_price: Money.optional(),
  min_accepted_price: Money.optional(), // sensível
  rent_price: Money.optional(),
  exclusive: z.boolean().default(false),
  exclusivity_until: dateOnly.nullish(),
  headline: z.string().nullish(),
  summary: z.string().nullish(),
  primary_broker_id: uuid.nullish(),
  published: z.boolean().default(false),
  last_price_change_at: datetime.nullish(),
  owners: z.array(PropertyOwnerLink).default([]),
  brokers: z.array(PropertyBrokerLink).default([]),
  intelligence: PropertyIntelligence.optional(),
  provenance: Provenance,
  audit: AuditStamp,
}).strict();

export const Listing = z.object({
  id: uuid,
  property_id: uuid,
  channel_id: uuid,
  locale: z.string(), // pt-BR, en-US
  transaction_type: TransactionType,
  title_public: z.string().nullish(),
  title_internal: z.string().nullish(),
  description_public: z.string().nullish(),
  description_internal: z.string().nullish(),
  price_display: PriceDisplay,
  display_price: Money.optional(),
  address_display: AddressDisplay,
  media_selection: z.array(uuid).default([]),
  listing_status: ListingStatus,
  exposure_level: ExposureLevel.optional(),
  published_at: datetime.nullish(),
  expires_at: datetime.nullish(),
  external_listing_id: z.string().nullish(),
  external_url: z.string().url().nullish(),
  provenance: Provenance,
  audit: AuditStamp,
}).strict();

export const Owner = z.object({
  id: uuid,
  owner_type: OwnerType,
  name: z.string(),
  legal_name: z.string().nullish(),
  tax_id: z.string().nullish(), // CPF/CNPJ — altamente confidencial
  email: z.string().email().nullish(),
  phone: z.string().nullish(),
  whatsapp: z.string().nullish(),
  address: Address.optional(),
  preferred_contact: z.string().nullish(),
  marketing_consent: z.boolean().default(false),
  notes: z.string().nullish(),
  provenance: Provenance,
  audit: AuditStamp,
}).strict();

export const Party = z.object({
  id: uuid,
  tenant_id: uuid.nullish(),
  party_type: PartyType,
  name: z.string(),
  legal_name: z.string().nullish(),
  tax_id: z.string().nullish(),
  email: z.string().email().nullish(),
  phone: z.string().nullish(),
  whatsapp: z.string().nullish(),
  address: Address.optional(),
  legal_basis: z.string().nullish(),
  processing_purpose: z.string().nullish(),
  retention_policy_id: uuid.nullish(),
  data_subject_request_ids: z.array(uuid).default([]),
  provenance: Provenance,
  audit: AuditStamp,
}).strict();

export const Ownership = z.object({
  id: uuid,
  party_id: uuid,
  unit_id: uuid.nullish(),
  property_id: uuid.nullish(),
  ownership_pct: z.number().min(0).max(100).nullish(),
  owner_role: OwnerRole.default("owner"),
  is_primary: z.boolean().default(false),
  starts_at: dateOnly.nullish(),
  ends_at: dateOnly.nullish(),
  provenance: Provenance,
  audit: AuditStamp,
}).strict();

export const Broker = z.object({
  id: uuid,
  name: z.string(),
  creci: z.string().nullish(),
  email: z.string().email().nullish(),
  phone: z.string().nullish(),
  team: z.string().nullish(),
  active: z.boolean().default(true),
  provenance: Provenance,
  audit: AuditStamp,
}).strict();

export const PublicationChannel = z.object({
  id: uuid,
  key: z.string(),
  name: z.string(),
  channel_type: ChannelType,
  config: z.record(z.string(), z.unknown()).optional(),
  active: z.boolean(),
}).strict();

export const MediaAsset = z.object({
  id: uuid,
  scope: z.enum(["building", "unit", "property", "listing"]),
  building_id: uuid.nullish(),
  unit_id: uuid.nullish(),
  property_id: uuid.nullish(),
  media_type: MediaType,
  media_role: MediaRole,
  url: z.string().url(),
  storage_key: z.string().nullish(),
  width: z.number().int().nullish(),
  height: z.number().int().nullish(),
  duration_s: z.number().int().nullish(),
  order_index: z.number().int().nullish(),
  caption: z.string().nullish(),
  media_rights: MediaRights.optional(),
  visibility: ExposureLevel.optional(),
  is_cover: z.boolean().default(false),
  checksum: z.string().nullish(),
  ai_tags: z.array(z.string()).default([]),
  provenance: Provenance,
  audit: AuditStamp,
}).strict();

export const Document = z.object({
  id: uuid,
  property_id: uuid.nullish(),
  unit_id: uuid.nullish(),
  owner_id: uuid.nullish(),
  document_type: DocumentType,
  title: z.string().nullish(),
  url: z.string().url().nullish(),
  storage_key: z.string().nullish(),
  confidentiality: Confidentiality.default("sensitive"),
  valid_until: dateOnly.nullish(),
  created_at: datetime,
  updated_at: datetime,
  version: z.number().int().min(1),
}).strict();

export const ExposureRule = z.object({
  id: uuid.optional(),
  property_id: uuid.nullish(),
  exposure_level: ExposureLevel,
  field_visibility: z.record(z.string(), z.string()).default({}),
  allowed_channels: z.array(z.string()).default([]),
  price_display: PriceDisplay.optional(),
  address_display: AddressDisplay.optional(),
  requires_approval: z.boolean().default(false),
}).strict();

export const ExposurePolicyRule = z.object({
  id: uuid.optional(),
  priority: z.number().int().default(0),
  effect: PolicyEffect,
  actions: z.array(PolicyAction),
  fields: z.array(z.string()).default([]),
  roles: z.array(z.string()).default([]),
  conditions: z.record(z.string(), z.unknown()).default({}),
  reason_code: z.string().nullish(),
}).strict();

export const ExposurePolicy = z.object({
  id: uuid,
  tenant_id: uuid.nullish(),
  resource_type: PolicyResourceType,
  resource_id: uuid.nullish(),
  exposure_level: ExposureLevel,
  rules: z.array(ExposurePolicyRule).default([]),
  requires_approval_for: z.array(PolicyAction).default([]),
  allowed_channels: z.array(z.string()).default([]),
  default_decision: PolicyDecision,
  audit_sensitive_reads: z.boolean(),
  created_at: datetime,
  updated_at: datetime,
}).strict();

export const DataSubjectRequest = z.object({
  id: uuid,
  tenant_id: uuid,
  party_id: uuid.nullish(),
  request_type: DataSubjectRequestType,
  status: DataSubjectRequestStatus,
  requested_at: datetime,
  due_at: datetime,
  fulfilled_at: datetime.nullish(),
  legal_basis: z.string().nullish(),
  processing_purpose: z.string().nullish(),
  audit_log_ref: z.string().nullish(),
  resolution_action: RetentionAction.nullish(),
  affected_record_ids: z.array(uuid).default([]),
  notes: z.string().nullish(),
}).strict();

export const RetentionPolicy = z.object({
  id: uuid,
  tenant_id: uuid,
  name: z.string(),
  legal_basis: z.string().nullish(),
  processing_purpose: z.string().nullish(),
  retention_period_days: z.number().int().min(0),
  action_on_expiry: RetentionAction,
  applies_to: z.array(z.string()).default([]),
  created_at: datetime,
  updated_at: datetime,
}).strict();

export const ImportSource = z.object({
  id: uuid,
  name: z.string(),
  source_system: SourceSystem,
  source_type: ImportSourceType,
  auth_type: z.string().nullish(),
  base_url: z.string().url().nullish(),
  active: z.boolean(),
  last_sync_at: datetime.nullish(),
  created_at: datetime,
  updated_at: datetime,
}).strict();

export const ImportBatch = z.object({
  id: uuid,
  source_id: uuid,
  status: ImportBatchStatus,
  file_name: z.string().nullish(),
  sync_batch_id: uuid.nullish(),
  total_rows: z.number().int().min(0).default(0),
  valid_rows: z.number().int().min(0).default(0),
  invalid_rows: z.number().int().min(0).default(0),
  duplicates_found: z.number().int().min(0).default(0),
  conflicts_found: z.number().int().min(0).default(0),
  started_at: datetime.nullish(),
  finished_at: datetime.nullish(),
  report_url: z.string().url().nullish(),
  created_by: z.string().nullish(),
}).strict();

export const ImportMapping = z.object({
  id: uuid,
  source_id: uuid,
  external_field: z.string(),
  pibras_field: z.string(),
  transform_rule: z.string().nullish(),
  required: z.boolean(),
  created_at: datetime,
  updated_at: datetime,
}).strict();

export const AuditEvent = z.object({
  id: z.number().int().optional(),
  entity_type: z.string(),
  entity_id: uuid,
  field: z.string().nullish(),
  old_value: z.unknown().nullish(),
  new_value: z.unknown().nullish(),
  change_type: AuditChangeType,
  source_system: SourceSystem.optional(),
  trust_tier: TrustTier.nullish(),
  actor: z.string().nullish(),
  sync_batch_id: uuid.nullish(),
  occurred_at: datetime,
}).strict();

/** Catálogo versionável de finalidades; não contém dados pessoais. */
export const ProcessingPurpose = z.object({
  id: uuid,
  tenant_id: uuid,
  code: z.string().min(1),
  name: z.string().min(1),
  description: z.string().min(1),
  data_categories: z.array(z.string()).min(1),
  retention_policy_id: uuid.nullish(),
  owner_role: z.string().min(1),
  active: z.boolean(),
  created_at: datetime,
  updated_at: datetime,
}).strict();

export const LegalBasisAssessment = z.object({
  id: uuid,
  tenant_id: uuid,
  processing_purpose_id: uuid,
  legal_basis: LegalBasisType,
  status: AssessmentStatus,
  rationale: z.string().min(1),
  safeguards: z.array(z.string()),
  evidence_ref: z.string().nullish(),
  assessed_by: z.string().min(1),
  assessed_at: datetime,
  expires_at: datetime.nullish(),
  updated_at: datetime,
}).strict();

export const PartnerRelationship = z.object({
  id: uuid,
  tenant_id: uuid,
  partner_organization_id: uuid,
  role: PartnerRole,
  contract_ref: z.string().min(1),
  dpa_ref: z.string().min(1),
  valid_from: dateOnly,
  valid_until: dateOnly.nullish(),
  dsar_contact_ref: z.string().nullish(),
  active: z.boolean(),
  created_at: datetime,
  updated_at: datetime,
}).strict();

export const FieldAllowlist = z.object({
  id: uuid,
  partner_relationship_id: uuid,
  processing_purpose_id: uuid,
  version: z.number().int().min(1),
  allowed_fields: z.array(z.string().min(1)).min(1),
  status: AllowlistStatus,
  approved_by: z.string().nullish(),
  approved_at: datetime.nullish(),
  effective_from: datetime,
  effective_until: datetime.nullish(),
  created_at: datetime,
  updated_at: datetime,
}).strict();

/** Ledger sem payload: registra apenas referências, campos e digest técnico. */
export const SharingEvent = z.object({
  id: uuid,
  tenant_id: uuid,
  partner_relationship_id: uuid,
  processing_purpose_id: uuid,
  legal_basis_assessment_id: uuid,
  field_allowlist_id: uuid,
  field_allowlist_version: z.number().int().min(1),
  shared_fields: z.array(z.string().min(1)).min(1),
  record_count: z.number().int().min(0),
  payload_digest: z.string().min(1),
  status: SharingEventStatus,
  correlation_id: z.string().min(1),
  occurred_at: datetime,
  failure_code: z.string().nullish(),
}).strict();

export const DSARPropagation = z.object({
  id: uuid,
  data_subject_request_id: uuid,
  partner_relationship_id: uuid,
  status: DSARPropagationStatus,
  action: RetentionAction,
  sent_at: datetime.nullish(),
  acknowledged_at: datetime.nullish(),
  fulfilled_at: datetime.nullish(),
  due_at: datetime,
  evidence_ref: z.string().nullish(),
  failure_code: z.string().nullish(),
  updated_at: datetime,
}).strict();

export const AutomatedDecisionRecord = z.object({
  id: uuid,
  tenant_id: uuid,
  processing_purpose_id: uuid,
  legal_basis_assessment_id: uuid,
  model_ref: z.string().min(1),
  model_version: z.string().min(1),
  input_categories: z.array(z.string()),
  outcome: AutomatedDecisionOutcome,
  sole_automated: z.boolean(),
  review_status: AutomatedReviewStatus,
  review_request_ref: z.string().nullish(),
  explanation_ref: z.string().nullish(),
  decided_at: datetime,
  reviewed_at: datetime.nullish(),
}).strict();

export const LegacyImportQualification = z.object({
  id: uuid,
  tenant_id: uuid,
  import_batch_id: uuid,
  processing_purpose_id: uuid,
  legal_basis_assessment_id: uuid,
  origin_verified: z.boolean(),
  purpose_compatible: z.boolean(),
  suppression_applied: z.boolean(),
  wave_number: z.number().int().min(1),
  record_count: z.number().int().min(0),
  status: LegacyQualificationStatus,
  evidence_ref: z.string().nullish(),
  assessed_by: z.string().min(1),
  assessed_at: datetime,
  updated_at: datetime,
}).strict();

export const ConformanceTestCase = z.object({
  id: z.string(),
  title: z.string(),
  version: z.string(),
  fixture_path: z.string(),
  expected_result: z.enum(["valid", "invalid"]),
  applies_to: z.array(z.string()).default([]),
}).strict();

export const Neighborhood = z.object({
  id: uuid,
  canonical_name: z.string(),
  aliases: z.array(z.string()).default([]),
  city: z.string().nullish(),
  state: z.string().length(2).nullish(),
  zone: z.string().nullish(),
  centroid_lat: z.number().nullish(),
  centroid_lng: z.number().nullish(),
  polygon: z.unknown().nullish(), // GeoJSON Polygon
  demand_index: z.number().nullish(),
  avg_price_m2: Money.optional(),
}).strict();

export const Geography = Neighborhood.extend({
  geography_type: GeographyType,
  parent_id: uuid.nullish(),
}).strict();

/* ------------------------------------------------------------------ *
 * Tipos inferidos
 * ------------------------------------------------------------------ */

export type Money = z.infer<typeof Money>;
export type ExternalId = z.infer<typeof ExternalId>;
export type Provenance = z.infer<typeof Provenance>;
export type AuditStamp = z.infer<typeof AuditStamp>;
export type Address = z.infer<typeof Address>;
export type Organization = z.infer<typeof Organization>;
export type Tenant = z.infer<typeof Tenant>;
export type User = z.infer<typeof User>;
export type Building = z.infer<typeof Building>;
export type Unit = z.infer<typeof Unit>;
export type Property = z.infer<typeof Property>;
export type PropertyIntelligence = z.infer<typeof PropertyIntelligence>;
export type Listing = z.infer<typeof Listing>;
export type Owner = z.infer<typeof Owner>;
export type Party = z.infer<typeof Party>;
export type Ownership = z.infer<typeof Ownership>;
export type Broker = z.infer<typeof Broker>;
export type PublicationChannel = z.infer<typeof PublicationChannel>;
export type MediaAsset = z.infer<typeof MediaAsset>;
export type Document = z.infer<typeof Document>;
export type ExposureRule = z.infer<typeof ExposureRule>;
export type ExposurePolicyRule = z.infer<typeof ExposurePolicyRule>;
export type ExposurePolicy = z.infer<typeof ExposurePolicy>;
export type DataSubjectRequest = z.infer<typeof DataSubjectRequest>;
export type RetentionPolicy = z.infer<typeof RetentionPolicy>;
export type ImportSource = z.infer<typeof ImportSource>;
export type ImportBatch = z.infer<typeof ImportBatch>;
export type ImportMapping = z.infer<typeof ImportMapping>;
export type AuditEvent = z.infer<typeof AuditEvent>;
export type ProcessingPurpose = z.infer<typeof ProcessingPurpose>;
export type LegalBasisAssessment = z.infer<typeof LegalBasisAssessment>;
export type PartnerRelationship = z.infer<typeof PartnerRelationship>;
export type FieldAllowlist = z.infer<typeof FieldAllowlist>;
export type SharingEvent = z.infer<typeof SharingEvent>;
export type DSARPropagation = z.infer<typeof DSARPropagation>;
export type AutomatedDecisionRecord = z.infer<typeof AutomatedDecisionRecord>;
export type LegacyImportQualification = z.infer<typeof LegacyImportQualification>;
export type ConformanceTestCase = z.infer<typeof ConformanceTestCase>;
export type Neighborhood = z.infer<typeof Neighborhood>;
export type Geography = z.infer<typeof Geography>;
export type PropertyOwnerLink = z.infer<typeof PropertyOwnerLink>;
export type PropertyBrokerLink = z.infer<typeof PropertyBrokerLink>;
