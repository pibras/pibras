-- PIBRAS aligned contract fixture (synthetic green).

CREATE TYPE audit_change_type AS ENUM ('create', 'update', 'delete', 'merge', 'split');

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    change_type audit_change_type NOT NULL,
    trust_tier SMALLINT CHECK (trust_tier BETWEEN 1 AND 6),
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE exposure_rule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exposure_level TEXT NOT NULL,
    field_visibility JSONB NOT NULL DEFAULT '{}'
);
