-- PIBRAS pre-reconciliation contract snapshot (frozen — never refresh).

CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL,
    change_type TEXT,
    trust_tier SMALLINT,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE exposure_rule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exposure_level TEXT NOT NULL,
    field_visibility JSONB NOT NULL DEFAULT '{}'
);
