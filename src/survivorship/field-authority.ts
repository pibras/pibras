import type { SourceSystem } from "../../types/mbras.ts";

export type FallbackAction = "pending_change" | "manual_approval" | "never_overwrite";

export interface FieldAuthorityRule {
  entity_type: string;
  field_path: string;
  /** Source systems that have direct write authority for this field. */
  authority_systems: SourceSystem[];
  /** What happens when a non-authoritative source tries to write. */
  fallback_action: FallbackAction;
}

/**
 * Default MBRAS Field Authority Matrix.
 * Defines per-field, per-entity write authority.
 * Lower trust tier systems attempting to write protected fields
 * will have their changes routed through the fallback_action.
 */
export const DEFAULT_AUTHORITY_MATRIX: FieldAuthorityRule[] = [
  // --- Property fields ---
  {
    entity_type: "property",
    field_path: "asking_price",
    authority_systems: ["mbras_internal", "twenty_crm"],
    fallback_action: "manual_approval",
  },
  {
    entity_type: "property",
    field_path: "asking_price_amount",
    authority_systems: ["mbras_internal", "twenty_crm"],
    fallback_action: "manual_approval",
  },
  {
    entity_type: "property",
    field_path: "min_accepted_price",
    authority_systems: ["mbras_internal"],
    fallback_action: "never_overwrite",
  },
  {
    entity_type: "property",
    field_path: "min_accepted_price_amount",
    authority_systems: ["mbras_internal"],
    fallback_action: "never_overwrite",
  },
  {
    entity_type: "property",
    field_path: "property_status",
    authority_systems: ["mbras_internal", "twenty_crm"],
    fallback_action: "pending_change",
  },
  {
    entity_type: "property",
    field_path: "exclusive",
    authority_systems: ["mbras_internal"],
    fallback_action: "pending_change",
  },
  {
    entity_type: "property",
    field_path: "exclusivity_until",
    authority_systems: ["mbras_internal"],
    fallback_action: "pending_change",
  },
  // headline and summary: any system at tier <= 4 can write
  {
    entity_type: "property",
    field_path: "headline",
    authority_systems: ["mbras_internal", "twenty_crm", "kenlo", "vista", "jetimob", "imobzi", "tecimob", "orulo"],
    fallback_action: "pending_change",
  },
  {
    entity_type: "property",
    field_path: "summary",
    authority_systems: ["mbras_internal", "twenty_crm", "kenlo", "vista", "jetimob", "imobzi", "tecimob", "orulo"],
    fallback_action: "pending_change",
  },

  // --- Unit fields ---
  {
    entity_type: "unit",
    field_path: "usable_area_m2",
    authority_systems: ["mbras_internal"],
    fallback_action: "pending_change",
  },
  {
    entity_type: "unit",
    field_path: "total_area_m2",
    authority_systems: ["mbras_internal"],
    fallback_action: "pending_change",
  },
  {
    entity_type: "unit",
    field_path: "matricula",
    authority_systems: ["mbras_internal"],
    fallback_action: "pending_change",
  },

  // --- Address fields (on any entity) ---
  {
    entity_type: "*",
    field_path: "address",
    authority_systems: ["mbras_internal"],
    fallback_action: "pending_change",
  },
  {
    entity_type: "*",
    field_path: "addr_street",
    authority_systems: ["mbras_internal"],
    fallback_action: "pending_change",
  },
  {
    entity_type: "*",
    field_path: "addr_number",
    authority_systems: ["mbras_internal"],
    fallback_action: "pending_change",
  },

  // --- Owner/Party PII fields ---
  {
    entity_type: "party",
    field_path: "tax_id",
    authority_systems: ["mbras_internal"],
    fallback_action: "never_overwrite",
  },
  {
    entity_type: "party",
    field_path: "name",
    authority_systems: ["mbras_internal"],
    fallback_action: "pending_change",
  },
  {
    entity_type: "party",
    field_path: "email",
    authority_systems: ["mbras_internal"],
    fallback_action: "pending_change",
  },
  {
    entity_type: "party",
    field_path: "phone",
    authority_systems: ["mbras_internal"],
    fallback_action: "pending_change",
  },
  {
    entity_type: "owner",
    field_path: "tax_id",
    authority_systems: ["mbras_internal"],
    fallback_action: "never_overwrite",
  },
  {
    entity_type: "owner",
    field_path: "name",
    authority_systems: ["mbras_internal"],
    fallback_action: "pending_change",
  },
];

/**
 * Resolves the authority rule for a specific entity type and field path.
 * Checks entity-specific rules first, then wildcard rules.
 * Returns undefined if no rule is defined (field is unprotected).
 */
export function resolveFieldAuthority(
  matrix: FieldAuthorityRule[],
  entityType: string,
  fieldPath: string
): FieldAuthorityRule | undefined {
  // 1. Exact entity + exact field
  const exact = matrix.find(
    (r) => r.entity_type === entityType && r.field_path === fieldPath
  );
  if (exact) return exact;

  // 2. Exact entity + prefix match (e.g. 'address' matches 'address.number')
  const prefixEntity = matrix.find(
    (r) => r.entity_type === entityType && fieldPath.startsWith(r.field_path + ".")
  );
  if (prefixEntity) return prefixEntity;

  // 3. Wildcard entity + exact field
  const wildcardExact = matrix.find(
    (r) => r.entity_type === "*" && r.field_path === fieldPath
  );
  if (wildcardExact) return wildcardExact;

  // 4. Wildcard entity + prefix match
  const wildcardPrefix = matrix.find(
    (r) => r.entity_type === "*" && fieldPath.startsWith(r.field_path + ".")
  );
  if (wildcardPrefix) return wildcardPrefix;

  return undefined;
}

/**
 * Checks if a given source system is authorized to write a field.
 */
export function isAuthorized(
  rule: FieldAuthorityRule,
  source: SourceSystem
): boolean {
  return rule.authority_systems.includes(source);
}
