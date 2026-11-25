BEGIN;
SET LOCAL search_path = mbras, public;
DO $$
DECLARE
  u uuid; p uuid; b uuid; other_b uuid; failed_constraint text;
BEGIN
  INSERT INTO building (name, src_system, trust_tier) VALUES ('Bloco A', 'manual', 2) RETURNING id INTO b;
  INSERT INTO building (name, src_system, trust_tier) VALUES ('Bloco B', 'manual', 2) RETURNING id INTO other_b;
  INSERT INTO unit (building_id, property_type, src_system, trust_tier)
    VALUES (b, 'apartment', 'manual', 2) RETURNING id INTO u;
  INSERT INTO property (unit_id, building_id, transaction_type, src_system, trust_tier)
    VALUES (u, b, 'sale', 'manual', 2) RETURNING id INTO p;
  SET CONSTRAINTS ALL IMMEDIATE;
  BEGIN
    UPDATE property SET unit_id=gen_random_uuid() WHERE id=p;
    RAISE EXCEPTION 'accepted nonexistent Unit';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
  BEGIN
    UPDATE property SET building_id=other_b WHERE id=p;
    RAISE EXCEPTION 'accepted mismatched buildings';
  EXCEPTION WHEN foreign_key_violation THEN
    GET STACKED DIAGNOSTICS failed_constraint = CONSTRAINT_NAME;
    IF failed_constraint <> 'property_unit_building_match' THEN RAISE; END IF;
  END;
  BEGIN
    UPDATE property SET building_id=NULL WHERE id=p;
    RAISE EXCEPTION 'accepted inconsistent NULL on Property';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
  BEGIN
    UPDATE unit SET building_id=NULL WHERE id=u;
    RAISE EXCEPTION 'accepted inconsistent NULL on Unit';
  EXCEPTION WHEN foreign_key_violation THEN NULL; END;
  -- Original ON DELETE SET NULL contract still permits building removal.
  SET CONSTRAINTS ALL DEFERRED;
  DELETE FROM building WHERE id=b;
  SET CONSTRAINTS ALL IMMEDIATE;
  IF (SELECT building_id FROM property WHERE id=p) IS NOT NULL OR
     (SELECT building_id FROM unit WHERE id=u) IS NOT NULL THEN
    RAISE EXCEPTION 'deleted building reference survived';
  END IF;
END $$;
ROLLBACK;
