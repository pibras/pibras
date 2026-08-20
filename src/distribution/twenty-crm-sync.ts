import { randomUUID } from "node:crypto";
import type {
  Property,
  Unit,
  MediaAsset,
  Address,
  Provenance,
} from "../../types/mbras.ts";
import { TRUST_TIERS } from "../../types/mbras.ts";
import {
  SurvivorshipArbitrator,
  type ArbitrationResult,
} from "../survivorship/arbitrator.ts";
import { RawReceiver } from "../ingestion/raw-receiver.ts";

export interface TwentyCRMPropertyPayload {
  id?: string | undefined;
  name?: string | undefined;
  pibrasPropertyId?: string | undefined;
  pibrasUnitId?: string | undefined;
  code?: string | undefined;
  status?: string | undefined;
  askingPriceAmount?: number | undefined;
  askingPriceCurrency?: string | undefined;
  rentPriceAmount?: number | undefined;
  condoFeeAmount?: number | undefined;
  iptuAnnualAmount?: number | undefined;
  usableAreaM2?: number | undefined;
  totalAreaM2?: number | undefined;
  bedrooms?: number | undefined;
  suites?: number | undefined;
  bathrooms?: number | undefined;
  parkingSpaces?: number | undefined;
  street?: string | undefined;
  number?: string | undefined;
  complement?: string | undefined;
  neighborhood?: string | undefined;
  city?: string | undefined;
  state?: string | undefined;
  postalCode?: string | undefined;
  photos?: Array<{ url: string; label?: string }> | undefined;
  exclusive?: boolean | undefined;
  headline?: string | undefined;
  summary?: string | undefined;
  updatedAt?: string | undefined;
  [key: string]: unknown;
}

export class TwentyCRMSync {
  /**
   * Converte uma Property + Unit canônicos para o payload do TwentyCRM.
   */
  public static toTwentyCRM(params: {
    property: Property;
    unit?: Unit | null | undefined;
    media_assets?: MediaAsset[] | undefined;
  }): TwentyCRMPropertyPayload {
    const p = params.property;
    const u = params.unit;
    const photos = (params.media_assets || []).map((m) => ({
      url: m.url,
      label: m.media_role,
    }));

    return {
      name: p.headline ?? `Imóvel ${p.code ?? p.id}`,
      pibrasPropertyId: p.id,
      pibrasUnitId: u?.id ?? undefined,
      code: p.code ?? undefined,
      status: p.property_status,
      askingPriceAmount: p.asking_price?.amount,
      askingPriceCurrency: p.asking_price?.currency,
      rentPriceAmount: p.rent_price?.amount,
      condoFeeAmount: u?.condo_fee?.amount,
      iptuAnnualAmount: u?.iptu_annual?.amount,
      usableAreaM2: u?.usable_area_m2 ?? undefined,
      totalAreaM2: u?.total_area_m2 ?? undefined,
      bedrooms: u?.bedrooms ?? undefined,
      suites: u?.suites ?? undefined,
      bathrooms: u?.bathrooms ?? undefined,
      parkingSpaces: u?.parking_spaces ?? undefined,
      street: u?.address?.street ?? undefined,
      number: u?.address?.number ?? undefined,
      complement: u?.address?.complement ?? undefined,
      neighborhood: u?.address?.neighborhood_raw ?? undefined,
      city: u?.address?.city ?? undefined,
      state: u?.address?.state ?? undefined,
      postalCode: u?.address?.postal_code ?? undefined,
      photos,
      exclusive: p.exclusive,
      headline: p.headline ?? undefined,
      summary: p.summary ?? undefined,
      updatedAt: p.audit.updated_at,
    };
  }

  /**
   * Ingesta um webhook ou atualização do TwentyCRM e executa a arbitragem de precedência contra os dados canônicos.
   */
  public static fromTwentyCRM(params: {
    twentyPayload: TwentyCRMPropertyPayload;
    currentProperty: Property | null;
    currentUnit: Unit | null;
    sync_batch_id?: string | null | undefined;
  }): {
    propertyArbitration: ArbitrationResult;
    unitArbitration?: ArbitrationResult | undefined;
    raw_receipt: ReturnType<typeof RawReceiver.receive>;
  } {
    const rawReceipt = RawReceiver.receive({
      source_system: "twenty_crm",
      source_record_id: params.twentyPayload.id ?? params.twentyPayload.code,
      payload: params.twentyPayload as Record<string, unknown>,
      sync_batch_id: params.sync_batch_id,
    });

    const incomingPropData: Record<string, unknown> = {};
    if (params.twentyPayload.status) incomingPropData["property_status"] = params.twentyPayload.status;
    if (params.twentyPayload.headline) incomingPropData["headline"] = params.twentyPayload.headline;
    if (params.twentyPayload.summary) incomingPropData["summary"] = params.twentyPayload.summary;
    if (params.twentyPayload.exclusive !== undefined) incomingPropData["exclusive"] = params.twentyPayload.exclusive;
    if (params.twentyPayload.askingPriceAmount !== undefined) {
      incomingPropData["asking_price"] = {
        amount: params.twentyPayload.askingPriceAmount,
        currency: (params.twentyPayload.askingPriceCurrency || "BRL") as "BRL" | "USD" | "EUR",
      };
    }

    const currentPropData = params.currentProperty ? (params.currentProperty as unknown as Record<string, unknown>) : null;
    const currentPropTier = params.currentProperty ? params.currentProperty.provenance.trust_tier : null;

    const propertyArbitration = SurvivorshipArbitrator.arbitrate({
      entity_type: "property",
      entity_id: params.currentProperty ? params.currentProperty.id : null,
      current_data: currentPropData,
      current_trust_tier: currentPropTier,
      incoming_data: incomingPropData,
      incoming_source: "twenty_crm",
      incoming_trust_tier: TRUST_TIERS.twenty_crm,
      ingestion_record_id: rawReceipt.ingestion_id,
    });

    let unitArbitration: ArbitrationResult | undefined;
    if (params.currentUnit) {
      const incomingUnitData: Record<string, unknown> = {};
      if (params.twentyPayload.bedrooms !== undefined) incomingUnitData["bedrooms"] = params.twentyPayload.bedrooms;
      if (params.twentyPayload.suites !== undefined) incomingUnitData["suites"] = params.twentyPayload.suites;
      if (params.twentyPayload.parkingSpaces !== undefined) incomingUnitData["parking_spaces"] = params.twentyPayload.parkingSpaces;
      if (params.twentyPayload.usableAreaM2 !== undefined) incomingUnitData["usable_area_m2"] = params.twentyPayload.usableAreaM2;

      unitArbitration = SurvivorshipArbitrator.arbitrate({
        entity_type: "unit",
        entity_id: params.currentUnit.id,
        current_data: params.currentUnit as unknown as Record<string, unknown>,
        current_trust_tier: params.currentUnit.provenance.trust_tier,
        incoming_data: incomingUnitData,
        incoming_source: "twenty_crm",
        incoming_trust_tier: TRUST_TIERS.twenty_crm,
        ingestion_record_id: rawReceipt.ingestion_id,
      });
    }

    return {
      propertyArbitration,
      unitArbitration,
      raw_receipt: rawReceipt,
    };
  }
}
