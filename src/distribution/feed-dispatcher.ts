import { createHash, randomUUID } from "node:crypto";
import type {
  SharingEvent,
  ChannelType,
} from "../../types/mbras.ts";
import type { FeedItemInput } from "./portal-xml-generator.ts";
import { PortalXMLGenerator } from "./portal-xml-generator.ts";

export interface DispatchParams {
  tenant_id: string;
  partner_relationship_id: string;
  processing_purpose_id: string;
  legal_basis_assessment_id: string;
  field_allowlist_id: string;
  field_allowlist_version: number;
  allowed_fields: string[];
  channel_type: ChannelType;
  items: FeedItemInput[];
  caller_role?: string | undefined;
}

export interface DispatchResult {
  sharing_event: SharingEvent;
  record_count: number;
  payload: string;
  channel_type: ChannelType;
}

export class FeedDispatcher {
  /**
   * Despacha um lote de imóveis para um canal de distribuição e gera o registro de auditoria SharingEvent (LGPD).
   */
  public static dispatch(params: DispatchParams): DispatchResult {
    const callerRole = params.caller_role ?? `${params.channel_type}_feed`;
    const xmlPayload = PortalXMLGenerator.generatePibrasXml(params.items, params.channel_type, callerRole);

    const now = new Date().toISOString();
    const digest = createHash("sha256").update(xmlPayload).digest("hex");
    const correlationId = `dispatch-${randomUUID()}`;

    const sharingEvent: SharingEvent = {
      id: randomUUID(),
      tenant_id: params.tenant_id,
      partner_relationship_id: params.partner_relationship_id,
      processing_purpose_id: params.processing_purpose_id,
      legal_basis_assessment_id: params.legal_basis_assessment_id,
      field_allowlist_id: params.field_allowlist_id,
      field_allowlist_version: params.field_allowlist_version,
      shared_fields: params.allowed_fields,
      record_count: params.items.length,
      payload_digest: digest,
      status: "delivered",
      correlation_id: correlationId,
      occurred_at: now,
      failure_code: null,
    };

    return {
      sharing_event: sharingEvent,
      record_count: params.items.length,
      payload: xmlPayload,
      channel_type: params.channel_type,
    };
  }
}
