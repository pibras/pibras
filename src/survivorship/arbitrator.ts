import { randomUUID } from "node:crypto";
import type { SourceSystem, TrustTier, RecordState } from "../../types/mbras.ts";
import { TRUST_TIERS } from "../../types/mbras.ts";
import { resolveFieldAuthority, isAuthorized, DEFAULT_AUTHORITY_MATRIX } from "./field-authority.ts";
import type { FieldAuthorityRule } from "./field-authority.ts";

export interface PendingChangeItem {
  id: string;
  entity_type: string;
  entity_id: string | null;
  proposed: Record<string, unknown>;
  current_snapshot: Record<string, unknown> | null;
  source_system: SourceSystem;
  trust_tier: TrustTier;
  ingestion_record_id: string | null;
  state: RecordState;
  conflict_reason: string | null;
  created_at: string;
  reviewed_by: string | null;
  reviewed_at: string | null;
}

export interface ArbitrationInput {
  entity_type: "property" | "unit" | "building" | "party";
  entity_id: string | null;
  current_data: Record<string, unknown> | null;
  current_trust_tier: TrustTier | null;
  incoming_data: Record<string, unknown>;
  incoming_source: SourceSystem;
  incoming_trust_tier: TrustTier;
  ingestion_record_id?: string | null | undefined;
  field_authority_matrix?: FieldAuthorityRule[];
}

export interface ArbitrationResult {
  action: "direct_apply" | "create_pending_change" | "mixed" | "noop";
  applied_data: Record<string, unknown>;
  pending_change: PendingChangeItem | null;
  reasons: string[];
}

export class SurvivorshipArbitrator {
  /**
   * Avalia a precedência e autoridade de dados entre a fonte externa e os dados canônicos existentes.
   * Regra de Ouro: Dados de fontes com menor autoridade (maior TrustTier) NUNCA sobrescrevem
   * dados proprietários sem gerar um PendingChange para revisão humana.
   */
  public static arbitrate(input: ArbitrationInput): ArbitrationResult {
    const now = new Date().toISOString();

    // 1. Novo registro: se não há registro atual, aceita diretamente
    if (!input.current_data || !input.entity_id) {
      return {
        action: "direct_apply",
        applied_data: input.incoming_data,
        pending_change: null,
        reasons: ["New entity creation: directly applying incoming payload"],
      };
    }

    const currentTier = input.current_trust_tier ?? TRUST_TIERS.spreadsheet_import;
    const incomingTier = input.incoming_trust_tier;

    // 2. Identificar campos com divergência (diff)
    const diffs: Record<string, unknown> = {};
    for (const [key, val] of Object.entries(input.incoming_data)) {
      if (val !== undefined && JSON.stringify(val) !== JSON.stringify(input.current_data[key])) {
        diffs[key] = val;
      }
    }

    if (Object.keys(diffs).length === 0) {
      return {
        action: "noop",
        applied_data: input.current_data,
        pending_change: null,
        reasons: ["No field differences detected"],
      };
    }

    // 3. Field Authority Matrix: evaluate per-field authority
    const matrix = input.field_authority_matrix ?? DEFAULT_AUTHORITY_MATRIX;
    const directFields: Record<string, unknown> = {};
    const pendingFields: Record<string, unknown> = {};
    const reasons: string[] = [];

    for (const [key, val] of Object.entries(diffs)) {
      const rule = resolveFieldAuthority(matrix, input.entity_type, key);

      if (!rule) {
        // No authority rule: fall back to trust tier comparison
        if (incomingTier <= currentTier) {
          directFields[key] = val;
          reasons.push(`Field '${key}': no authority rule; trust tier ${incomingTier} <= ${currentTier}, applying directly.`);
        } else {
          pendingFields[key] = val;
          reasons.push(`Field '${key}': no authority rule; trust tier ${incomingTier} > ${currentTier}, routing to PendingChange.`);
        }
      } else if (isAuthorized(rule, input.incoming_source)) {
        // Source is authorized for this field
        directFields[key] = val;
        reasons.push(`Field '${key}': source '${input.incoming_source}' is authorized (authority_systems: [${rule.authority_systems.join(", ")}]).`);
      } else {
        // Source is NOT authorized
        if (rule.fallback_action === "never_overwrite") {
          reasons.push(`Field '${key}': BLOCKED. Source '${input.incoming_source}' cannot modify (fallback: never_overwrite).`);
        } else {
          pendingFields[key] = val;
          reasons.push(`Field '${key}': routed to ${rule.fallback_action}. Source '${input.incoming_source}' lacks authority (authority_systems: [${rule.authority_systems.join(", ")}]).`);
        }
      }
    }

    // 4. Build result based on what ended up where
    const hasDirectFields = Object.keys(directFields).length > 0;
    const hasPendingFields = Object.keys(pendingFields).length > 0;

    let pendingChange: PendingChangeItem | null = null;
    if (hasPendingFields) {
      pendingChange = {
        id: randomUUID(),
        entity_type: input.entity_type,
        entity_id: input.entity_id,
        proposed: pendingFields,
        current_snapshot: input.current_data,
        source_system: input.incoming_source,
        trust_tier: incomingTier,
        ingestion_record_id: input.ingestion_record_id ?? null,
        state: "pending_review",
        conflict_reason: `Field-level authority: ${Object.keys(pendingFields).length} field(s) require review. Source '${input.incoming_source}' (tier ${incomingTier}) lacks authority.`,
        created_at: now,
        reviewed_by: null,
        reviewed_at: null,
      };
    }

    const updatedData = { ...input.current_data, ...directFields };

    if (hasDirectFields && hasPendingFields) {
      return { action: "mixed", applied_data: updatedData, pending_change: pendingChange, reasons };
    }
    if (hasDirectFields) {
      return { action: "direct_apply", applied_data: updatedData, pending_change: null, reasons };
    }
    return { action: "create_pending_change", applied_data: input.current_data, pending_change: pendingChange, reasons };
  }
}
