-- =====================================================================
-- Padrão PIBRAS de Dados Imobiliários — Modelo Canônico (Postgres / Neon)
-- Versão 0.1.0 · 2026-06-18
-- Fonte de verdade: docs/PROPERTY-STANDARD-v0.1.md
--
-- Convenções:
--   * dinheiro: <campo>_amount BIGINT (centavos) + <campo>_currency currency
--   * instantes: TIMESTAMPTZ (UTC) · datas: DATE · áreas: NUMERIC (m²)
--   * toda entidade primária carrega provenance (src_*) e audit (created_at...)
-- =====================================================================

BEGIN;

CREATE SCHEMA IF NOT EXISTS mbras;
SET search_path TO mbras, public;

-- gen_random_uuid() é nativo no Postgres >= 13. Em versões antigas: CREATE EXTENSION pgcrypto.

-- ---------------------------------------------------------------------
-- Enums canônicos
-- ---------------------------------------------------------------------
CREATE TYPE source_system   AS ENUM ('mbras_internal','twenty_crm','kenlo','vista','jetimob','imobzi','tecimob','orulo','zap_vivareal','olx','xml_generic','csv_import','excel_import','manual','other');
CREATE TYPE record_state    AS ENUM ('draft','pending_review','active','conflict','duplicate','rejected','archived');
CREATE TYPE property_type   AS ENUM ('apartment','penthouse','house','house_condo','studio','loft','flat','land','farm','commercial_room','commercial_building','warehouse','hotel','whole_building','other');
CREATE TYPE transaction_type AS ENUM ('sale','rent','sale_rent','season_rent');
CREATE TYPE property_status AS ENUM ('draft','available','reserved','under_offer','sold','rented','suspended','off_market','archived');
CREATE TYPE availability    AS ENUM ('available','unavailable','conditioned');
CREATE TYPE currency        AS ENUM ('BRL','USD','EUR');
CREATE TYPE exposure_level  AS ENUM ('public','restricted','confidential','off_market');
CREATE TYPE confidentiality AS ENUM ('normal','sensitive','highly_confidential');
CREATE TYPE media_type      AS ENUM ('photo','video','floor_plan','virtual_tour','document','aerial');
CREATE TYPE media_role      AS ENUM ('cover','gallery','floor_plan','facade','common_area','view','amenity','other');
CREATE TYPE media_rights    AS ENUM ('owned','licensed','restricted');
CREATE TYPE media_scope     AS ENUM ('building','unit','property','listing');
CREATE TYPE channel_type    AS ENUM ('website','portal','crm','broker_network','off_market_pdf','paid_ad','landing_page','whatsapp','email');
CREATE TYPE owner_type      AS ENUM ('individual','company');
CREATE TYPE owner_role      AS ENUM ('owner','representative','heir','attorney');
CREATE TYPE broker_role     AS ENUM ('listing','co_listing','capture');
CREATE TYPE document_type   AS ENUM ('matricula','iptu','contrato','escritura','laudo_avaliacao','planta_aprovada','habite_se','other');
CREATE TYPE listing_status  AS ENUM ('draft','published','paused','expired','removed');
CREATE TYPE price_display   AS ENUM ('visible','on_request');
CREATE TYPE address_display AS ENUM ('full','approximate','hidden');
CREATE TYPE sun_orientation AS ENUM ('morning','afternoon','full_day','none');
CREATE TYPE building_status AS ENUM ('planning','under_construction','ready');
CREATE TYPE geo_precision   AS ENUM ('exact','approximate','neighborhood','none');
CREATE TYPE computed_by     AS ENUM ('human','agent','hermes');
CREATE TYPE geography_type  AS ENUM ('country','state','city','zone','neighborhood','microregion','condominium_region');
CREATE TYPE party_type      AS ENUM ('individual','company');
CREATE TYPE policy_effect   AS ENUM ('allow','deny');
CREATE TYPE policy_action   AS ENUM ('read','write','publish','export','send','approve');
CREATE TYPE policy_decision AS ENUM ('allow','deny','mask','needs_approval');
CREATE TYPE policy_resource_type AS ENUM ('unit','property','listing','media','document','party','price','address');
CREATE TYPE dedupe_review_state AS ENUM ('unreviewed','auto_matched','needs_review','confirmed_duplicate','confirmed_unique');
CREATE TYPE dsar_request_type AS ENUM ('access','correction','deletion','portability','objection');
CREATE TYPE dsar_status AS ENUM ('received','verifying_identity','in_progress','fulfilled','rejected','expired');
CREATE TYPE retention_action AS ENUM ('delete','anonymize','review','archive');
CREATE TYPE import_source_type AS ENUM ('api','csv','excel','xml','database_dump','manual');
CREATE TYPE import_batch_status AS ENUM ('draft','mapping','validating','reviewing','imported','failed','cancelled');
CREATE TYPE lead_stage      AS ENUM ('new','qualified','engaged','negotiating','won','lost');
CREATE TYPE visit_status    AS ENUM ('scheduled','done','no_show','cancelled');
CREATE TYPE offer_status    AS ENUM ('submitted','countered','accepted','rejected','withdrawn');

-- ---------------------------------------------------------------------
-- Gatilho genérico: updated_at + version++
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION touch_row() RETURNS trigger AS $$
BEGIN
  NEW.updated_at := now();
  NEW.version    := COALESCE(OLD.version, 0) + 1;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE organization (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  legal_name      TEXT,
  tax_id          TEXT,
  website_url     TEXT,
  country         CHAR(2) NOT NULL DEFAULT 'BR',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  version         INTEGER NOT NULL DEFAULT 1
);
CREATE TRIGGER trg_organization_touch BEFORE UPDATE ON organization FOR EACH ROW EXECUTE FUNCTION touch_row();

CREATE TABLE tenant (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id UUID NOT NULL REFERENCES organization(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  data_controller_tenant_id UUID REFERENCES tenant(id) ON DELETE SET NULL,
  data_processor_org_id UUID REFERENCES organization(id) ON DELETE SET NULL,
  retention_policy_id UUID,  -- FK -> retention_policy.id (soft ref; evita ciclo de DDL)
  international_transfer_allowed BOOLEAN NOT NULL DEFAULT false,
  active          BOOLEAN NOT NULL DEFAULT true,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  version         INTEGER NOT NULL DEFAULT 1,
  UNIQUE (organization_id, name)
);
CREATE TRIGGER trg_tenant_touch BEFORE UPDATE ON tenant FOR EACH ROW EXECUTE FUNCTION touch_row();

CREATE TABLE retention_policy (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
  name            TEXT NOT NULL,
  legal_basis     TEXT,
  processing_purpose TEXT,
  retention_period_days INTEGER NOT NULL CHECK (retention_period_days >= 0),
  action_on_expiry retention_action NOT NULL,
  applies_to      TEXT[] NOT NULL DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  version         INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX idx_retention_policy_tenant ON retention_policy(tenant_id);
CREATE TRIGGER trg_retention_policy_touch BEFORE UPDATE ON retention_policy FOR EACH ROW EXECUTE FUNCTION touch_row();

CREATE TABLE "user" (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID REFERENCES tenant(id) ON DELETE SET NULL,
  organization_id UUID REFERENCES organization(id) ON DELETE SET NULL,
  name            TEXT NOT NULL,
  email           TEXT,
  roles           TEXT[] NOT NULL DEFAULT '{}',
  active          BOOLEAN NOT NULL DEFAULT true,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  version         INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX idx_user_tenant ON "user"(tenant_id);
CREATE INDEX idx_user_organization ON "user"(organization_id);
CREATE TRIGGER trg_user_touch BEFORE UPDATE ON "user" FOR EACH ROW EXECUTE FUNCTION touch_row();

-- =====================================================================
-- Neighborhood (referência de normalização)
-- =====================================================================
CREATE TABLE neighborhood (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  canonical_name  TEXT NOT NULL,
  aliases         TEXT[] NOT NULL DEFAULT '{}',
  city            TEXT,
  state           CHAR(2),
  zone            TEXT,
  centroid_lat    DOUBLE PRECISION,
  centroid_lng    DOUBLE PRECISION,
  polygon         JSONB,                  -- GeoJSON Polygon
  demand_index    NUMERIC,
  avg_price_m2_amount   BIGINT,
  avg_price_m2_currency currency DEFAULT 'BRL',
  UNIQUE (canonical_name, city, state)
);
CREATE INDEX idx_neighborhood_aliases ON neighborhood USING GIN (aliases);

CREATE TABLE geography (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  geography_type  geography_type NOT NULL DEFAULT 'neighborhood',
  parent_id       UUID REFERENCES geography(id) ON DELETE SET NULL,
  canonical_name  TEXT NOT NULL,
  aliases         TEXT[] NOT NULL DEFAULT '{}',
  city            TEXT,
  state           CHAR(2),
  zone            TEXT,
  centroid_lat    DOUBLE PRECISION,
  centroid_lng    DOUBLE PRECISION,
  polygon         JSONB,
  demand_index    NUMERIC,
  avg_price_m2_amount   BIGINT,
  avg_price_m2_currency currency DEFAULT 'BRL',
  UNIQUE (geography_type, canonical_name, city, state)
);
CREATE INDEX idx_geography_aliases ON geography USING GIN (aliases);
CREATE INDEX idx_geography_parent ON geography(parent_id);

-- =====================================================================
-- Building / Condomínio
-- =====================================================================
CREATE TABLE building (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  developer       TEXT,
  -- address (embutido)
  addr_street     TEXT,
  addr_number     TEXT,
  addr_complement TEXT,
  addr_neighborhood_id UUID REFERENCES neighborhood(id),
  addr_neighborhood_raw TEXT,
  addr_city       TEXT,
  addr_state      CHAR(2),
  addr_postal_code TEXT,
  addr_country    CHAR(2) NOT NULL DEFAULT 'BR',
  addr_latitude   DOUBLE PRECISION,
  addr_longitude  DOUBLE PRECISION,
  addr_geo_precision geo_precision,
  building_status building_status,
  year_built      INTEGER,
  delivery_date   DATE,
  floors          INTEGER,
  towers          INTEGER,
  total_units     INTEGER,
  amenities       TEXT[] NOT NULL DEFAULT '{}',
  description     TEXT,
  -- provenance
  src_system      source_system NOT NULL,
  src_record_id   TEXT,
  src_url         TEXT,
  trust_tier      SMALLINT NOT NULL CHECK (trust_tier BETWEEN 1 AND 6),
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  ingested_by     TEXT,
  sync_batch_id   UUID,
  raw_payload_ref TEXT,
  -- audit
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by      TEXT,
  updated_by      TEXT,
  version         INTEGER NOT NULL DEFAULT 1,
  record_state    record_state NOT NULL DEFAULT 'active',
  completeness_score SMALLINT CHECK (completeness_score BETWEEN 0 AND 100),
  data_quality    JSONB,
  UNIQUE (src_system, src_record_id)
);
CREATE TRIGGER trg_building_touch BEFORE UPDATE ON building FOR EACH ROW EXECUTE FUNCTION touch_row();

-- =====================================================================
-- Unit (identidade física durável)
-- =====================================================================
CREATE TABLE unit (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  building_id     UUID REFERENCES building(id) ON DELETE SET NULL,
  matricula       TEXT,                   -- chave durável de identidade física
  dedupe_key      TEXT,
  normalized_address_key TEXT,
  area_signature  TEXT,
  duplicate_of_unit_id UUID REFERENCES unit(id) ON DELETE SET NULL,
  dedupe_confidence NUMERIC CHECK (dedupe_confidence >= 0 AND dedupe_confidence <= 1),
  dedupe_review_state dedupe_review_state NOT NULL DEFAULT 'unreviewed',
  property_type   property_type NOT NULL,
  -- address próprio (casa/terreno); senão herda do building
  addr_street     TEXT,
  addr_number     TEXT,
  addr_complement TEXT,
  addr_neighborhood_id UUID REFERENCES neighborhood(id),
  addr_neighborhood_raw TEXT,
  addr_city       TEXT,
  addr_state      CHAR(2),
  addr_postal_code TEXT,
  addr_country    CHAR(2) DEFAULT 'BR',
  addr_latitude   DOUBLE PRECISION,
  addr_longitude  DOUBLE PRECISION,
  addr_geo_precision geo_precision,
  unit_number     TEXT,
  tower           TEXT,
  floor           INTEGER,
  usable_area_m2  NUMERIC CHECK (usable_area_m2 >= 0),
  total_area_m2   NUMERIC CHECK (total_area_m2 >= 0),
  lot_area_m2     NUMERIC CHECK (lot_area_m2 >= 0),
  bedrooms        INTEGER CHECK (bedrooms >= 0),
  suites          INTEGER CHECK (suites >= 0),
  bathrooms       INTEGER CHECK (bathrooms >= 0),
  parking_spaces  INTEGER CHECK (parking_spaces >= 0),
  sun_orientation sun_orientation,
  view_type       TEXT,
  ceiling_height_m NUMERIC CHECK (ceiling_height_m >= 0),
  features        TEXT[] NOT NULL DEFAULT '{}',
  condo_fee_amount    BIGINT,
  condo_fee_currency  currency DEFAULT 'BRL',
  iptu_annual_amount   BIGINT,
  iptu_annual_currency currency DEFAULT 'BRL',
  -- provenance
  src_system      source_system NOT NULL,
  src_record_id   TEXT,
  src_url         TEXT,
  trust_tier      SMALLINT NOT NULL CHECK (trust_tier BETWEEN 1 AND 6),
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  ingested_by     TEXT,
  sync_batch_id   UUID,
  raw_payload_ref TEXT,
  -- audit
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by      TEXT,
  updated_by      TEXT,
  version         INTEGER NOT NULL DEFAULT 1,
  record_state    record_state NOT NULL DEFAULT 'active',
  completeness_score SMALLINT CHECK (completeness_score BETWEEN 0 AND 100),
  data_quality    JSONB
);
CREATE INDEX idx_unit_building ON unit(building_id);
CREATE INDEX idx_unit_matricula ON unit(matricula) WHERE matricula IS NOT NULL;
CREATE INDEX idx_unit_dedupe_key ON unit(dedupe_key) WHERE dedupe_key IS NOT NULL;
CREATE INDEX idx_unit_normalized_address_key ON unit(normalized_address_key) WHERE normalized_address_key IS NOT NULL;
CREATE INDEX idx_unit_geo ON unit(addr_latitude, addr_longitude);
CREATE TRIGGER trg_unit_touch BEFORE UPDATE ON unit FOR EACH ROW EXECUTE FUNCTION touch_row();

-- =====================================================================
-- Owner (PII sensível)
-- =====================================================================
CREATE TABLE owner (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_type      owner_type NOT NULL,
  name            TEXT NOT NULL,
  legal_name      TEXT,
  tax_id          TEXT,                   -- CPF/CNPJ — altamente confidencial
  email           TEXT,
  phone           TEXT,
  whatsapp        TEXT,
  addr_street     TEXT,
  addr_number     TEXT,
  addr_complement TEXT,
  addr_neighborhood_id UUID REFERENCES geography(id) ON DELETE SET NULL,
  addr_neighborhood_raw TEXT,
  addr_city       TEXT,
  addr_state      CHAR(2),
  addr_postal_code TEXT,
  addr_country    CHAR(2) DEFAULT 'BR',
  addr_latitude   DOUBLE PRECISION CHECK (addr_latitude BETWEEN -90 AND 90),
  addr_longitude  DOUBLE PRECISION CHECK (addr_longitude BETWEEN -180 AND 180),
  addr_geo_precision geo_precision,
  addr_formatted  TEXT,
  preferred_contact TEXT,
  marketing_consent BOOLEAN NOT NULL DEFAULT false,
  notes           TEXT,
  src_system      source_system NOT NULL,
  src_record_id   TEXT,
  trust_tier      SMALLINT NOT NULL CHECK (trust_tier BETWEEN 1 AND 6),
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  ingested_by     TEXT,
  sync_batch_id   UUID,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by      TEXT,
  updated_by      TEXT,
  version         INTEGER NOT NULL DEFAULT 1,
  record_state    record_state NOT NULL DEFAULT 'active'
);
CREATE INDEX idx_owner_tax_id ON owner(tax_id) WHERE tax_id IS NOT NULL;
CREATE TRIGGER trg_owner_touch BEFORE UPDATE ON owner FOR EACH ROW EXECUTE FUNCTION touch_row();

-- =====================================================================
-- Broker
-- =====================================================================
CREATE TABLE broker (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  creci       TEXT,
  email       TEXT,
  phone       TEXT,
  team        TEXT,
  active      BOOLEAN NOT NULL DEFAULT true,
  src_system  source_system NOT NULL DEFAULT 'mbras_internal',
  trust_tier  SMALLINT NOT NULL DEFAULT 2 CHECK (trust_tier BETWEEN 1 AND 6),
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  version     INTEGER NOT NULL DEFAULT 1,
  record_state record_state NOT NULL DEFAULT 'active'
);
CREATE TRIGGER trg_broker_touch BEFORE UPDATE ON broker FOR EACH ROW EXECUTE FUNCTION touch_row();

-- =====================================================================
-- Property (registro de inventário)
-- =====================================================================
CREATE TABLE property (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code            TEXT,
  unit_id         UUID NOT NULL REFERENCES unit(id) ON DELETE RESTRICT,
  building_id     UUID REFERENCES building(id) ON DELETE SET NULL,
  transaction_type transaction_type NOT NULL,
  property_status property_status NOT NULL DEFAULT 'draft',
  availability    availability,
  asking_price_amount    BIGINT,
  asking_price_currency  currency DEFAULT 'BRL',
  min_accepted_price_amount   BIGINT,     -- sensível
  min_accepted_price_currency currency DEFAULT 'BRL',
  rent_price_amount      BIGINT,
  rent_price_currency    currency DEFAULT 'BRL',
  exclusive       BOOLEAN NOT NULL DEFAULT false,
  exclusivity_until DATE,
  headline        TEXT,
  summary         TEXT,
  primary_broker_id UUID REFERENCES broker(id) ON DELETE SET NULL,
  published       BOOLEAN NOT NULL DEFAULT false,
  last_price_change_at TIMESTAMPTZ,
  -- provenance
  src_system      source_system NOT NULL,
  src_record_id   TEXT,
  src_url         TEXT,
  trust_tier      SMALLINT NOT NULL CHECK (trust_tier BETWEEN 1 AND 6),
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  ingested_by     TEXT,
  sync_batch_id   UUID,
  raw_payload_ref TEXT,
  -- audit
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by      TEXT,
  updated_by      TEXT,
  version         INTEGER NOT NULL DEFAULT 1,
  record_state    record_state NOT NULL DEFAULT 'active',
  completeness_score SMALLINT CHECK (completeness_score BETWEEN 0 AND 100),
  data_quality    JSONB,
  UNIQUE (src_system, src_record_id)
);
CREATE INDEX idx_property_unit ON property(unit_id);
CREATE UNIQUE INDEX idx_property_code_unique ON property(code) WHERE code IS NOT NULL;
CREATE INDEX idx_property_status ON property(property_status);
CREATE INDEX idx_property_record_state ON property(record_state);
CREATE INDEX idx_property_txn ON property(transaction_type);
CREATE TRIGGER trg_property_touch BEFORE UPDATE ON property FOR EACH ROW EXECUTE FUNCTION touch_row();

CREATE TABLE property_external_id (
  property_id   UUID NOT NULL REFERENCES property(id) ON DELETE CASCADE,
  namespace     TEXT NOT NULL,
  key           TEXT NOT NULL,
  value         TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (property_id, namespace, key, value)
);
CREATE INDEX idx_property_external_id_lookup ON property_external_id(namespace, key, value);

-- =====================================================================
-- PropertyIntelligence (1:1 com Property — camada premium)
-- =====================================================================
CREATE TABLE property_intelligence (
  property_id     UUID PRIMARY KEY REFERENCES property(id) ON DELETE CASCADE,
  ideal_buyer_profile TEXT,
  likely_objections  TEXT[] NOT NULL DEFAULT '{}',
  selling_arguments  TEXT[] NOT NULL DEFAULT '{}',
  privacy_level   TEXT,
  rarity_score    SMALLINT CHECK (rarity_score BETWEEN 0 AND 100),
  architecture_notes TEXT,
  view_quality    SMALLINT CHECK (view_quality BETWEEN 0 AND 100),
  natural_light   SMALLINT CHECK (natural_light BETWEEN 0 AND 100),
  noise_level     SMALLINT CHECK (noise_level BETWEEN 0 AND 100),
  liquidity_score SMALLINT CHECK (liquidity_score BETWEEN 0 AND 100),
  match_score     SMALLINT CHECK (match_score BETWEEN 0 AND 100),
  defensible_price_amount   BIGINT,
  defensible_price_currency currency DEFAULT 'BRL',
  off_market_potential SMALLINT CHECK (off_market_potential BETWEEN 0 AND 100),
  demand_notes    TEXT,
  last_computed_at TIMESTAMPTZ,
  computed_by     computed_by,
  confidence      SMALLINT CHECK (confidence BETWEEN 0 AND 100)
);

-- =====================================================================
-- Vínculos N:N
-- =====================================================================
CREATE TABLE property_owners (
  property_id   UUID NOT NULL REFERENCES property(id) ON DELETE CASCADE,
  owner_id      UUID NOT NULL REFERENCES owner(id) ON DELETE CASCADE,
  ownership_pct NUMERIC CHECK (ownership_pct BETWEEN 0 AND 100),
  owner_role    owner_role NOT NULL DEFAULT 'owner',
  is_primary    BOOLEAN NOT NULL DEFAULT false,
  PRIMARY KEY (property_id, owner_id)
);

CREATE TABLE party (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID REFERENCES tenant(id) ON DELETE SET NULL,
  party_type      party_type NOT NULL,
  name            TEXT NOT NULL,
  legal_name      TEXT,
  tax_id          TEXT,
  email           TEXT,
  phone           TEXT,
  whatsapp        TEXT,
  addr_street     TEXT,
  addr_number     TEXT,
  addr_complement TEXT,
  addr_neighborhood_id UUID REFERENCES geography(id) ON DELETE SET NULL,
  addr_neighborhood_raw TEXT,
  addr_city       TEXT,
  addr_state      CHAR(2),
  addr_postal_code TEXT,
  addr_country    CHAR(2) DEFAULT 'BR',
  addr_latitude   DOUBLE PRECISION CHECK (addr_latitude BETWEEN -90 AND 90),
  addr_longitude  DOUBLE PRECISION CHECK (addr_longitude BETWEEN -180 AND 180),
  addr_geo_precision geo_precision,
  addr_formatted  TEXT,
  legal_basis     TEXT,
  processing_purpose TEXT,
  retention_policy_id UUID,  -- FK -> retention_policy.id (soft ref)
  data_subject_request_ids UUID[] NOT NULL DEFAULT '{}',
  src_system      source_system NOT NULL,
  src_record_id   TEXT,
  trust_tier      SMALLINT NOT NULL CHECK (trust_tier BETWEEN 1 AND 6),
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  ingested_by     TEXT,
  sync_batch_id   UUID,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by      TEXT,
  updated_by      TEXT,
  version         INTEGER NOT NULL DEFAULT 1,
  record_state    record_state NOT NULL DEFAULT 'active'
);
CREATE INDEX idx_party_tax_id ON party(tax_id) WHERE tax_id IS NOT NULL;
CREATE INDEX idx_party_tenant ON party(tenant_id);
CREATE TRIGGER trg_party_touch BEFORE UPDATE ON party FOR EACH ROW EXECUTE FUNCTION touch_row();

CREATE TABLE ownership (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  party_id      UUID NOT NULL REFERENCES party(id) ON DELETE CASCADE,
  unit_id       UUID REFERENCES unit(id) ON DELETE CASCADE,
  property_id   UUID REFERENCES property(id) ON DELETE CASCADE,
  ownership_pct NUMERIC CHECK (ownership_pct BETWEEN 0 AND 100),
  owner_role    owner_role NOT NULL DEFAULT 'owner',
  is_primary    BOOLEAN NOT NULL DEFAULT false,
  starts_at     DATE,
  ends_at       DATE,
  src_system    source_system NOT NULL,
  src_record_id TEXT,
  trust_tier    SMALLINT NOT NULL CHECK (trust_tier BETWEEN 1 AND 6),
  ingested_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  version       INTEGER NOT NULL DEFAULT 1,
  record_state  record_state NOT NULL DEFAULT 'active',
  CHECK (unit_id IS NOT NULL OR property_id IS NOT NULL)
);
CREATE INDEX idx_ownership_party ON ownership(party_id);
CREATE INDEX idx_ownership_unit ON ownership(unit_id);
CREATE INDEX idx_ownership_property ON ownership(property_id);
CREATE TRIGGER trg_ownership_touch BEFORE UPDATE ON ownership FOR EACH ROW EXECUTE FUNCTION touch_row();

CREATE TABLE property_brokers (
  property_id  UUID NOT NULL REFERENCES property(id) ON DELETE CASCADE,
  broker_id    UUID NOT NULL REFERENCES broker(id) ON DELETE CASCADE,
  broker_role  broker_role NOT NULL DEFAULT 'listing',
  is_primary   BOOLEAN NOT NULL DEFAULT false,
  assigned_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (property_id, broker_id)
);

-- =====================================================================
-- PublicationChannel + Listing
-- =====================================================================
CREATE TABLE publication_channel (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  key          TEXT NOT NULL UNIQUE,      -- website_mbras, zap, vivareal, olx, broker_net, offmarket_pdf, meta_ads
  name         TEXT NOT NULL,
  channel_type channel_type NOT NULL,
  config       JSONB,
  active       BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE listing (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id     UUID NOT NULL REFERENCES property(id) ON DELETE CASCADE,
  channel_id      UUID NOT NULL REFERENCES publication_channel(id) ON DELETE RESTRICT,
  locale          TEXT NOT NULL DEFAULT 'pt-BR',
  transaction_type transaction_type NOT NULL,
  title_public    TEXT,
  title_internal  TEXT,
  description_public  TEXT,
  description_internal TEXT,
  price_display   price_display NOT NULL DEFAULT 'visible',
  display_price_amount   BIGINT,
  display_price_currency currency DEFAULT 'BRL',
  address_display address_display NOT NULL DEFAULT 'full',
  media_selection UUID[] NOT NULL DEFAULT '{}',
  listing_status  listing_status NOT NULL DEFAULT 'draft',
  exposure_level  exposure_level,
  published_at    TIMESTAMPTZ,
  expires_at      TIMESTAMPTZ,
  external_listing_id TEXT,
  external_url    TEXT,
  src_system      source_system NOT NULL DEFAULT 'mbras_internal',
  trust_tier      SMALLINT NOT NULL DEFAULT 2 CHECK (trust_tier BETWEEN 1 AND 6),
  ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  version         INTEGER NOT NULL DEFAULT 1,
  record_state    record_state NOT NULL DEFAULT 'active',
  UNIQUE (property_id, channel_id, locale)
);
CREATE INDEX idx_listing_property ON listing(property_id);
CREATE INDEX idx_listing_channel ON listing(channel_id);
CREATE INDEX idx_listing_status ON listing(listing_status);
CREATE TRIGGER trg_listing_touch BEFORE UPDATE ON listing FOR EACH ROW EXECUTE FUNCTION touch_row();

-- =====================================================================
-- MediaAsset
-- =====================================================================
CREATE TABLE media_asset (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scope        media_scope NOT NULL,
  building_id  UUID REFERENCES building(id) ON DELETE CASCADE,
  unit_id      UUID REFERENCES unit(id) ON DELETE CASCADE,
  property_id  UUID REFERENCES property(id) ON DELETE CASCADE,
  media_type   media_type NOT NULL,
  media_role   media_role NOT NULL DEFAULT 'gallery',
  url          TEXT NOT NULL,
  storage_key  TEXT,
  width        INTEGER,
  height       INTEGER,
  duration_s   INTEGER,
  order_index  INTEGER,
  caption      TEXT,
  media_rights media_rights DEFAULT 'owned',
  visibility   exposure_level DEFAULT 'public',
  is_cover     BOOLEAN NOT NULL DEFAULT false,
  checksum     TEXT,                      -- hash perceptual/MD5 para dedupe
  ai_tags      TEXT[] NOT NULL DEFAULT '{}',
  src_system   source_system NOT NULL DEFAULT 'mbras_internal',
  trust_tier   SMALLINT NOT NULL DEFAULT 2 CHECK (trust_tier BETWEEN 1 AND 6),
  ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  version      INTEGER NOT NULL DEFAULT 1,
  record_state record_state NOT NULL DEFAULT 'active',
  CHECK (
    (scope = 'building'  AND building_id IS NOT NULL) OR
    (scope = 'unit'      AND unit_id     IS NOT NULL) OR
    (scope IN ('property','listing') AND property_id IS NOT NULL)
  )
);
CREATE INDEX idx_media_building ON media_asset(building_id);
CREATE INDEX idx_media_unit ON media_asset(unit_id);
CREATE INDEX idx_media_property ON media_asset(property_id);
CREATE INDEX idx_media_checksum ON media_asset(checksum) WHERE checksum IS NOT NULL;
CREATE TRIGGER trg_media_touch BEFORE UPDATE ON media_asset FOR EACH ROW EXECUTE FUNCTION touch_row();

-- =====================================================================
-- Document
-- =====================================================================
CREATE TABLE document (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id   UUID REFERENCES property(id) ON DELETE CASCADE,
  unit_id       UUID REFERENCES unit(id) ON DELETE CASCADE,
  owner_id      UUID REFERENCES owner(id) ON DELETE CASCADE,
  document_type document_type NOT NULL,
  title         TEXT,
  url           TEXT,
  storage_key   TEXT,
  confidentiality confidentiality NOT NULL DEFAULT 'sensitive',
  valid_until   DATE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  version       INTEGER NOT NULL DEFAULT 1
);
CREATE TRIGGER trg_document_touch BEFORE UPDATE ON document FOR EACH ROW EXECUTE FUNCTION touch_row();

-- =====================================================================
-- ExposureRule
-- =====================================================================
CREATE TABLE exposure_rule (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id     UUID REFERENCES property(id) ON DELETE CASCADE,  -- NULL = regra default por nível
  exposure_level  exposure_level NOT NULL,
  field_visibility JSONB NOT NULL DEFAULT '{}',  -- { "address.number": "director", "owner": "broker" }
  allowed_channels TEXT[] NOT NULL DEFAULT '{}',
  price_display   price_display,
  address_display address_display,
  requires_approval BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX idx_exposure_property ON exposure_rule(property_id);

CREATE TABLE exposure_policy (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID REFERENCES tenant(id) ON DELETE SET NULL,
  resource_type   policy_resource_type NOT NULL,
  resource_id     UUID,
  exposure_level  exposure_level NOT NULL,
  rules           JSONB NOT NULL DEFAULT '[]',
  requires_approval_for policy_action[] NOT NULL DEFAULT '{}',
  allowed_channels TEXT[] NOT NULL DEFAULT '{}',
  default_decision policy_decision NOT NULL DEFAULT 'deny',
  audit_sensitive_reads BOOLEAN NOT NULL DEFAULT true,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  version         INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX idx_exposure_policy_resource ON exposure_policy(resource_type, resource_id);
CREATE INDEX idx_exposure_policy_tenant ON exposure_policy(tenant_id);
CREATE TRIGGER trg_exposure_policy_touch BEFORE UPDATE ON exposure_policy FOR EACH ROW EXECUTE FUNCTION touch_row();

-- =====================================================================
-- LeadInterest · Visit · Offer (eventos comerciais)
-- =====================================================================
CREATE TABLE lead_interest (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id   UUID NOT NULL REFERENCES property(id) ON DELETE CASCADE,
  contact_name  TEXT,
  contact_email TEXT,
  contact_phone TEXT,
  lead_stage    lead_stage NOT NULL DEFAULT 'new',
  score         SMALLINT CHECK (score BETWEEN 0 AND 100),
  match_score   SMALLINT CHECK (match_score BETWEEN 0 AND 100),
  source        source_system,
  crm_external_id TEXT,
  notes         TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_lead_property ON lead_interest(property_id);

CREATE TABLE visit (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id   UUID NOT NULL REFERENCES property(id) ON DELETE CASCADE,
  lead_ref      TEXT,
  broker_id     UUID REFERENCES broker(id) ON DELETE SET NULL,
  scheduled_at  TIMESTAMPTZ,
  visit_status  visit_status NOT NULL DEFAULT 'scheduled',
  feedback      TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE offer (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id   UUID NOT NULL REFERENCES property(id) ON DELETE CASCADE,
  buyer_ref     TEXT,
  amount        BIGINT,
  currency      currency DEFAULT 'BRL',
  offer_status  offer_status NOT NULL DEFAULT 'submitted',
  conditions    TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  decided_at    TIMESTAMPTZ
);

CREATE TABLE data_subject_request (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id     UUID NOT NULL REFERENCES tenant(id) ON DELETE CASCADE,
  party_id      UUID REFERENCES party(id) ON DELETE SET NULL,
  request_type  dsar_request_type NOT NULL,
  status        dsar_status NOT NULL DEFAULT 'received',
  requested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  due_at        TIMESTAMPTZ NOT NULL,
  fulfilled_at  TIMESTAMPTZ,
  legal_basis   TEXT,
  processing_purpose TEXT,
  audit_log_ref TEXT,
  resolution_action retention_action,
  affected_record_ids UUID[] NOT NULL DEFAULT '{}',
  notes         TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  version       INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX idx_dsr_tenant ON data_subject_request(tenant_id);
CREATE INDEX idx_dsr_party ON data_subject_request(party_id);
CREATE INDEX idx_dsr_status ON data_subject_request(status);
CREATE TRIGGER trg_dsr_touch BEFORE UPDATE ON data_subject_request FOR EACH ROW EXECUTE FUNCTION touch_row();

CREATE TABLE import_source (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT NOT NULL,
  source_system source_system NOT NULL,
  source_type   import_source_type NOT NULL,
  auth_type     TEXT,
  base_url      TEXT,
  active        BOOLEAN NOT NULL DEFAULT true,
  last_sync_at  TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  version       INTEGER NOT NULL DEFAULT 1
);
CREATE TRIGGER trg_import_source_touch BEFORE UPDATE ON import_source FOR EACH ROW EXECUTE FUNCTION touch_row();

CREATE TABLE import_batch (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id     UUID NOT NULL REFERENCES import_source(id) ON DELETE CASCADE,
  status        import_batch_status NOT NULL DEFAULT 'draft',
  file_name     TEXT,
  sync_batch_id UUID,
  total_rows    INTEGER NOT NULL DEFAULT 0 CHECK (total_rows >= 0),
  valid_rows    INTEGER NOT NULL DEFAULT 0 CHECK (valid_rows >= 0),
  invalid_rows  INTEGER NOT NULL DEFAULT 0 CHECK (invalid_rows >= 0),
  duplicates_found INTEGER NOT NULL DEFAULT 0 CHECK (duplicates_found >= 0),
  conflicts_found INTEGER NOT NULL DEFAULT 0 CHECK (conflicts_found >= 0),
  started_at    TIMESTAMPTZ,
  finished_at   TIMESTAMPTZ,
  report_url    TEXT,
  created_by    TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_import_batch_source ON import_batch(source_id);
CREATE INDEX idx_import_batch_sync ON import_batch(sync_batch_id);

CREATE TABLE import_mapping (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id     UUID NOT NULL REFERENCES import_source(id) ON DELETE CASCADE,
  external_field TEXT NOT NULL,
  pibras_field  TEXT NOT NULL,
  transform_rule TEXT,
  required      BOOLEAN NOT NULL DEFAULT false,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  version       INTEGER NOT NULL DEFAULT 1,
  UNIQUE (source_id, external_field, pibras_field)
);
CREATE INDEX idx_import_mapping_source ON import_mapping(source_id);
CREATE TRIGGER trg_import_mapping_touch BEFORE UPDATE ON import_mapping FOR EACH ROW EXECUTE FUNCTION touch_row();

-- =====================================================================
-- ComparableProperty
-- =====================================================================
CREATE TABLE comparable_property (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  property_id   UUID NOT NULL REFERENCES property(id) ON DELETE CASCADE,
  addr_formatted TEXT,
  area_m2       NUMERIC,
  price_amount  BIGINT,
  price_currency currency DEFAULT 'BRL',
  sold_at       DATE,
  source        source_system,
  similarity_score SMALLINT CHECK (similarity_score BETWEEN 0 AND 100),
  notes         TEXT
);
CREATE INDEX idx_comparable_property ON comparable_property(property_id);

-- =====================================================================
-- Trilhas de histórico
-- =====================================================================
CREATE TABLE price_history (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  property_id   UUID NOT NULL REFERENCES property(id) ON DELETE CASCADE,
  old_amount    BIGINT,
  new_amount    BIGINT,
  currency      currency NOT NULL DEFAULT 'BRL',
  changed_by    TEXT,
  source_system source_system,
  trust_tier    SMALLINT,
  reason        TEXT,
  changed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_price_hist_property ON price_history(property_id, changed_at DESC);

CREATE TABLE status_history (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  property_id   UUID NOT NULL REFERENCES property(id) ON DELETE CASCADE,
  old_status    property_status,
  new_status    property_status,
  changed_by    TEXT,
  source_system source_system,
  reason        TEXT,
  changed_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_status_hist_property ON status_history(property_id, changed_at DESC);

-- =====================================================================
-- audit_log genérico (toda entidade, mudança campo a campo)
-- =====================================================================
CREATE TABLE audit_log (
  id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  entity_type   TEXT NOT NULL,
  entity_id     UUID NOT NULL,
  field         TEXT,
  old_value     JSONB,
  new_value     JSONB,
  change_type   TEXT,                     -- insert | update | delete
  source_system source_system,
  trust_tier    SMALLINT,
  actor         TEXT,
  sync_batch_id UUID,
  occurred_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id, occurred_at DESC);

-- =====================================================================
-- Governança de ingestão: registro bruto + mudanças pendentes / conflitos
-- =====================================================================
CREATE TABLE ingestion_record (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_system source_system NOT NULL,
  source_record_id TEXT,
  sync_batch_id UUID,
  payload       JSONB NOT NULL,           -- payload bruto como recebido
  received_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  processed     BOOLEAN NOT NULL DEFAULT false,
  processing_error TEXT
);
CREATE INDEX idx_ingestion_batch ON ingestion_record(sync_batch_id);
CREATE INDEX idx_ingestion_unprocessed ON ingestion_record(processed) WHERE processed = false;

-- Diffs propostos aguardando aprovação (regra de ouro: externo entra como sugestão)
CREATE TABLE pending_change (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_type   TEXT NOT NULL,
  entity_id     UUID,                     -- NULL se for criação de novo registro
  proposed      JSONB NOT NULL,           -- diff proposto (campo -> novo valor)
  current_snapshot JSONB,                 -- estado atual, para o revisor comparar
  source_system source_system NOT NULL,
  trust_tier    SMALLINT NOT NULL,
  ingestion_record_id UUID REFERENCES ingestion_record(id) ON DELETE SET NULL,
  state         record_state NOT NULL DEFAULT 'pending_review',  -- pending_review | conflict | rejected
  conflict_reason TEXT,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewed_by   TEXT,
  reviewed_at   TIMESTAMPTZ
);
CREATE INDEX idx_pending_entity ON pending_change(entity_type, entity_id);
CREATE INDEX idx_pending_state ON pending_change(state);

CREATE TABLE conformance_test_case (
  id              TEXT PRIMARY KEY,
  title           TEXT NOT NULL,
  version         TEXT NOT NULL,
  fixture_path    TEXT NOT NULL,
  expected_result TEXT NOT NULL CHECK (expected_result IN ('valid','invalid')),
  applies_to      TEXT[] NOT NULL DEFAULT '{}',
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- =====================================================================
-- Read model: view de leitura property_full (site / portais / CRM)
-- ExposureRule segue compatível; ExposurePolicy é o alvo v0.2 na borda de leitura.
-- =====================================================================
CREATE MATERIALIZED VIEW property_full AS
SELECT
  p.id,
  p.code,
  p.transaction_type,
  p.property_status,
  p.availability,
  p.asking_price_amount,
  p.asking_price_currency,
  p.exclusive,
  p.published,
  u.id            AS unit_id,
  u.property_type,
  u.matricula,
  u.usable_area_m2,
  u.total_area_m2,
  u.bedrooms,
  u.suites,
  u.bathrooms,
  u.parking_spaces,
  u.sun_orientation,
  u.view_type,
  COALESCE(u.addr_city,    b.addr_city)    AS city,
  COALESCE(u.addr_state,   b.addr_state)   AS state,
  COALESCE(u.addr_neighborhood_id, b.addr_neighborhood_id) AS neighborhood_id,
  COALESCE(u.addr_latitude,  b.addr_latitude)  AS latitude,
  COALESCE(u.addr_longitude, b.addr_longitude) AS longitude,
  b.id            AS building_id,
  b.name          AS building_name,
  b.amenities,
  pi.liquidity_score,
  pi.match_score,
  pi.rarity_score,
  pi.off_market_potential,
  p.record_state,
  p.completeness_score,
  p.updated_at
FROM property p
JOIN unit u            ON u.id = p.unit_id
LEFT JOIN building b   ON b.id = COALESCE(p.building_id, u.building_id)
LEFT JOIN property_intelligence pi ON pi.property_id = p.id
WHERE p.record_state = 'active';

CREATE UNIQUE INDEX idx_property_full_id ON property_full(id);
CREATE INDEX idx_property_full_city ON property_full(city, state);
CREATE INDEX idx_property_full_price ON property_full(asking_price_amount);
-- Atualize com: REFRESH MATERIALIZED VIEW CONCURRENTLY mbras.property_full;

COMMIT;
