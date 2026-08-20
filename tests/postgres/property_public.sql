\set ON_ERROR_STOP on

BEGIN;
SET search_path TO mbras, public;

INSERT INTO building (
  id, name, addr_city, addr_state, addr_latitude, addr_longitude,
  amenities, src_system, trust_tier
) VALUES (
  '10000000-0000-4000-8000-000000000001', 'Edifício Teste', 'São Paulo', 'SP',
  -23.5842317, -46.6812449, ARRAY['piscina'], 'manual', 2
);

INSERT INTO unit (
  id, building_id, property_type, usable_area_m2, bedrooms,
  src_system, trust_tier
) VALUES (
  '10000000-0000-4000-8000-000000000002',
  '10000000-0000-4000-8000-000000000001',
  'apartment', 220, 3, 'manual', 2
);

INSERT INTO property (
  id, code, unit_id, building_id, transaction_type, property_status,
  availability, asking_price_amount, asking_price_currency, published,
  src_system, trust_tier
) VALUES (
  '10000000-0000-4000-8000-000000000003', 'PUBLIC-TEST',
  '10000000-0000-4000-8000-000000000002',
  '10000000-0000-4000-8000-000000000001',
  'sale', 'available', 'available', 1750000000, 'BRL', true, 'manual', 2
);

INSERT INTO publication_channel (id, key, name, channel_type, active)
VALUES (
  '10000000-0000-4000-8000-000000000004',
  'public_test', 'Canal público de teste', 'website', true
);

INSERT INTO listing (
  id, property_id, channel_id, transaction_type, price_display,
  address_display, listing_status, exposure_level
) VALUES (
  '10000000-0000-4000-8000-000000000005',
  '10000000-0000-4000-8000-000000000003',
  '10000000-0000-4000-8000-000000000004',
  'sale', 'visible', 'full', 'published', 'public'
);

DO $$
DECLARE projected RECORD;
BEGIN
  SELECT * INTO STRICT projected
  FROM property_public
  WHERE id = '10000000-0000-4000-8000-000000000003';

  IF projected.latitude_approx <> -23.58 OR projected.longitude_approx <> -46.68 THEN
    RAISE EXCEPTION 'public coordinates were not reduced: %, %',
      projected.latitude_approx, projected.longitude_approx;
  END IF;
  IF projected.asking_price_amount <> 1750000000 OR projected.building_name <> 'Edifício Teste' THEN
    RAISE EXCEPTION 'public price/building projection is incorrect';
  END IF;
END;
$$;

-- Base-table updates must appear immediately; no materialized-view refresh.
UPDATE building
SET addr_latitude = -23.5967, addr_longitude = -46.6941
WHERE id = '10000000-0000-4000-8000-000000000001';

DO $$
DECLARE projected RECORD;
BEGIN
  SELECT * INTO STRICT projected FROM property_public
  WHERE id = '10000000-0000-4000-8000-000000000003';
  IF projected.latitude_approx <> -23.60 OR projected.longitude_approx <> -46.69 THEN
    RAISE EXCEPTION 'public projection is stale: %, %',
      projected.latitude_approx, projected.longitude_approx;
  END IF;
END;
$$;

UPDATE listing
SET price_display = 'on_request', address_display = 'hidden'
WHERE id = '10000000-0000-4000-8000-000000000005';

DO $$
DECLARE projected RECORD;
BEGIN
  SELECT * INTO STRICT projected FROM property_public
  WHERE id = '10000000-0000-4000-8000-000000000003';
  IF projected.asking_price_amount IS NOT NULL OR projected.asking_price_currency IS NOT NULL THEN
    RAISE EXCEPTION 'on_request listing exposed price';
  END IF;
  IF projected.city IS NOT NULL OR projected.state IS NOT NULL
     OR projected.neighborhood_id IS NOT NULL
     OR projected.latitude_approx IS NOT NULL OR projected.longitude_approx IS NOT NULL
     OR projected.building_name IS NOT NULL THEN
    RAISE EXCEPTION 'hidden listing exposed location';
  END IF;
END;
$$;

-- NULL/restricted exposure is fail-closed.
UPDATE listing
SET exposure_level = NULL, address_display = 'approximate'
WHERE id = '10000000-0000-4000-8000-000000000005';
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM property_public WHERE id = '10000000-0000-4000-8000-000000000003') THEN
    RAISE EXCEPTION 'NULL exposure listing entered property_public';
  END IF;
END;
$$;

UPDATE listing SET exposure_level = 'restricted'
WHERE id = '10000000-0000-4000-8000-000000000005';
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM property_public WHERE id = '10000000-0000-4000-8000-000000000003') THEN
    RAISE EXCEPTION 'restricted listing entered property_public';
  END IF;
END;
$$;

UPDATE listing SET exposure_level = 'public'
WHERE id = '10000000-0000-4000-8000-000000000005';
UPDATE property SET published = false
WHERE id = '10000000-0000-4000-8000-000000000003';
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM property_public WHERE id = '10000000-0000-4000-8000-000000000003') THEN
    RAISE EXCEPTION 'revoked property remained public';
  END IF;
END;
$$;

ROLLBACK;
