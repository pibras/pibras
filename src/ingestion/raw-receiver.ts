import { createHash, randomUUID } from "node:crypto";
import type { SourceSystem, TrustTier, Provenance } from "../../types/mbras.ts";
import { TRUST_TIERS } from "../../types/mbras.ts";

export interface RawIngestionPayload {
  source_system: SourceSystem;
  source_record_id?: string | null | undefined;
  source_url?: string | null | undefined;
  payload: Record<string, unknown> | Array<Record<string, unknown>>;
  ingested_by?: string | null | undefined;
  sync_batch_id?: string | null | undefined;
}

export interface IngestionReceipt {
  ingestion_id: string;
  source_system: SourceSystem;
  source_record_id?: string | null | undefined;
  payload_sha256: string;
  record_count: number;
  trust_tier: TrustTier;
  ingested_at: string;
  provenance: Provenance;
  payload: Record<string, unknown> | Array<Record<string, unknown>>;
}

/**
 * Resolves default trust tier based on source system.
 * Lower number = higher trust authority.
 */
export function resolveSourceTrustTier(source: SourceSystem): TrustTier {
  switch (source) {
    case "mbras_internal":
    case "manual":
      return TRUST_TIERS.mbras_internal;
    case "twenty_crm":
      return TRUST_TIERS.twenty_crm;
    case "kenlo":
    case "vista":
    case "jetimob":
    case "imobzi":
    case "tecimob":
    case "orulo":
      return TRUST_TIERS.external_primary;
    case "zap_vivareal":
    case "olx":
    case "xml_generic":
      return TRUST_TIERS.xml_feed;
    case "csv_import":
    case "excel_import":
    default:
      return TRUST_TIERS.spreadsheet_import;
  }
}

/**
 * Computes SHA-256 deterministic hash of payload.
 */
export function computePayloadDigest(data: unknown): string {
  const jsonStr = JSON.stringify(data, Object.keys(data as object).sort());
  return createHash("sha256").update(jsonStr).digest("hex");
}

/**
 * Ingestion receiver: persists raw payloads immutably and constructs provenance.
 */
export class RawReceiver {
  public static receive(input: RawIngestionPayload): IngestionReceipt {
    const now = new Date().toISOString();
    const digest = computePayloadDigest(input.payload);
    const count = Array.isArray(input.payload) ? input.payload.length : 1;
    const tier = resolveSourceTrustTier(input.source_system);
    const ingestionId = randomUUID();

    const provenance: Provenance = {
      source_system: input.source_system,
      source_record_id: input.source_record_id ?? null,
      source_url: input.source_url ?? null,
      trust_tier: tier,
      ingested_at: now,
      ingested_by: input.ingested_by ?? null,
      sync_batch_id: input.sync_batch_id ?? null,
      raw_payload_ref: `ingestion://${ingestionId}/${digest}`,
    };

    return {
      ingestion_id: ingestionId,
      source_system: input.source_system,
      source_record_id: input.source_record_id ?? null,
      payload_sha256: digest,
      record_count: count,
      trust_tier: tier,
      ingested_at: now,
      provenance,
      payload: input.payload,
    };
  }
}
