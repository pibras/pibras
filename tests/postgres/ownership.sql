-- A03 corpus, coownership case: store real legacy rows, lift them into the
-- canonical relations, compare both persisted endpoints to the golden result.
BEGIN;
SET LOCAL search_path = mbras, public;
CREATE TEMP TABLE fixture AS SELECT :'ownership_fixture'::jsonb AS doc;
CREATE TEMP VIEW corpus AS SELECT doc->'entities' AS e FROM fixture;
CREATE TEMP VIEW coownership AS
SELECT c FROM fixture, jsonb_array_elements(doc->'cases') c WHERE c->>'name'='coownership';
INSERT INTO unit (id, property_type, src_system, trust_tier)
SELECT (e->>'unitA')::uuid, 'land', 'manual', 2 FROM corpus;
INSERT INTO property (id, unit_id, transaction_type, src_system, src_record_id, trust_tier, ingested_at,
                      created_at, updated_at, version, record_state)
SELECT (e->>'propertyA')::uuid, (e->>'unitA')::uuid, 'sale',
       (p->>'source_system')::source_system, p->>'source_record_id',
       (p->>'trust_tier')::smallint, (p->>'ingested_at')::timestamptz,
       (e#>>'{propertyEvidence,audit,created_at}')::timestamptz, (e#>>'{propertyEvidence,audit,updated_at}')::timestamptz,
       (e#>>'{propertyEvidence,audit,version}')::int, (e#>>'{propertyEvidence,audit,record_state}')::record_state
FROM corpus, LATERAL (SELECT e#>'{propertyEvidence,provenance}' AS p) src;

INSERT INTO owner (id, name, owner_type, notes, marketing_consent, src_system,
                   src_record_id, trust_tier, ingested_at, created_at, updated_at, version, record_state)
SELECT (v->>'id')::uuid, v->>'name', (v->>'owner_type')::owner_type, v->>'notes',
       (v->>'marketing_consent')::boolean, (v#>>'{provenance,source_system}')::source_system,
       v#>>'{provenance,source_record_id}', (v#>>'{provenance,trust_tier}')::smallint,
       (v#>>'{provenance,ingested_at}')::timestamptz, (v#>>'{audit,created_at}')::timestamptz,
       (v#>>'{audit,updated_at}')::timestamptz, (v#>>'{audit,version}')::int, (v#>>'{audit,record_state}')::record_state
FROM corpus, coownership, jsonb_array_elements_text(c->'owners') k,
     LATERAL (SELECT e->k AS v) data;

INSERT INTO property_owners (property_id, owner_id, ownership_pct, owner_role, is_primary)
SELECT r.property_id, r.owner_id, r.ownership_pct, r.owner_role, r.is_primary
FROM corpus, coownership, jsonb_array_elements_text(c->'links') k,
     jsonb_populate_record(NULL::property_owners, e->k) r;

INSERT INTO party (id, name, party_type, src_system, src_record_id, trust_tier,
                   ingested_at, created_at, updated_at, version, record_state)
SELECT id, name, owner_type::text::party_type, src_system, src_record_id, trust_tier,
       ingested_at, created_at, updated_at, version, record_state FROM owner;

-- The fixture supplies the migration profile's IDs; SQL checks persistence,
-- not the separate A03 UUID derivation algorithm.
INSERT INTO ownership (id, property_id, party_id, ownership_pct, owner_role, is_primary,
                       src_system, src_record_id, trust_tier, ingested_at, created_at, updated_at, version, record_state)
SELECT (v->>'id')::uuid, l.property_id, l.owner_id, l.ownership_pct, l.owner_role,
       l.is_primary, p.src_system, p.src_record_id, p.trust_tier, p.ingested_at,
       p.created_at, p.updated_at, p.version, p.record_state
FROM corpus, coownership, jsonb_array_elements_text(c->'expected_ownerships') k,
     LATERAL (SELECT e->k AS v) data
JOIN property_owners l ON l.owner_id=(v->>'party_id')::uuid AND l.property_id=(v->>'property_id')::uuid
JOIN property p ON p.id=l.property_id;
SET CONSTRAINTS ALL IMMEDIATE;

DO $$
BEGIN
  IF (SELECT count(*) FROM ownership) <> 2 OR (SELECT count(*) FROM party) <> 2 OR EXISTS (
    SELECT 1 FROM corpus, coownership, jsonb_array_elements_text(c->'expected_ownerships') k,
    LATERAL (SELECT e->k AS v) data
    LEFT JOIN ownership o ON o.id=(v->>'id')::uuid
    WHERE (o.party_id,o.property_id,o.ownership_pct,o.owner_role::text,o.is_primary,
           o.src_system::text,o.src_record_id,o.trust_tier,o.ingested_at,o.created_at,o.updated_at,o.version,o.record_state::text)
      IS DISTINCT FROM ((v->>'party_id')::uuid,(v->>'property_id')::uuid,(v->>'ownership_pct')::numeric,
         v->>'owner_role',(v->>'is_primary')::boolean,v#>>'{provenance,source_system}',
         v#>>'{provenance,source_record_id}',(v#>>'{provenance,trust_tier}')::smallint,
         (v#>>'{provenance,ingested_at}')::timestamptz,(v#>>'{audit,created_at}')::timestamptz,
         (v#>>'{audit,updated_at}')::timestamptz,(v#>>'{audit,version}')::int,v#>>'{audit,record_state}')
  ) OR EXISTS (
    SELECT 1 FROM corpus, coownership, jsonb_array_elements_text(c->'expected_parties') k,
    LATERAL (SELECT e->k AS v) data LEFT JOIN party p ON p.id=(v->>'id')::uuid
    WHERE (p.name,p.party_type::text,p.src_system::text,p.src_record_id,p.trust_tier,p.ingested_at)
    IS DISTINCT FROM (v->>'name',v->>'party_type',v#>>'{provenance,source_system}',v#>>'{provenance,source_record_id}',
       (v#>>'{provenance,trust_tier}')::smallint,(v#>>'{provenance,ingested_at}')::timestamptz)
  ) THEN RAISE EXCEPTION 'legacy coownership or provenance did not match the A03 corpus'; END IF;
END $$;

DO $$
DECLARE link uuid := (SELECT id FROM ownership ORDER BY id LIMIT 1);
BEGIN
  BEGIN
    UPDATE ownership SET ownership_pct=ownership_pct+1 WHERE id=link;
    RAISE EXCEPTION 'accepted total >100';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM NOT LIKE 'aggregate ownership for this resource%exceeding 100' THEN RAISE; END IF;
  END;
  BEGIN
    UPDATE ownership SET unit_id=(SELECT id FROM unit) WHERE id=link;
    RAISE EXCEPTION 'accepted ownership with both targets';
  EXCEPTION WHEN check_violation THEN NULL; END;
  BEGIN
    UPDATE ownership SET property_id=NULL WHERE id=link;
    RAISE EXCEPTION 'accepted ownership with no target';
  EXCEPTION WHEN check_violation THEN NULL; END;
  BEGIN
    UPDATE ownership SET party_id=gen_random_uuid() WHERE id=link;
    RAISE EXCEPTION 'accepted nonexistent Party';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
  BEGIN
    UPDATE property_owners SET owner_id=gen_random_uuid();
    RAISE EXCEPTION 'accepted nonexistent legacy Owner';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
END $$;

-- New links to a physical Unit do not share the Property percentage budget.
INSERT INTO ownership (id, party_id, unit_id, ownership_pct, owner_role, is_primary,
                       src_system, src_record_id, trust_tier, ingested_at)
SELECT r.id, r.party_id, r.unit_id, r.ownership_pct, r.owner_role, r.is_primary,
       (p->>'source_system')::source_system, p->>'source_record_id',
       (p->>'trust_tier')::smallint, (p->>'ingested_at')::timestamptz
FROM corpus, jsonb_populate_record(NULL::ownership, e->'unitOwnershipA') r,
     LATERAL (SELECT e#>'{unitOwnershipA,provenance}' AS p) src;
ROLLBACK;
