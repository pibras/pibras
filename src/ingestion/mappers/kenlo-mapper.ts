import { randomUUID } from "node:crypto";
import type {
  Unit,
  Property,
  Address,
  MediaAsset,
  PropertyType,
  TransactionType,
  PropertyStatus,
  AuditStamp,
} from "../../../types/mbras.ts";
import {
  buildUnitDedupeKey,
  buildNormalizedAddressKey,
  buildAreaSignature,
} from "../../dedupe/normalizer.ts";
import { parseBRLToCentavos, parseAreaM2, parseInteger } from "./generic-csv-mapper.ts";
import { RawReceiver } from "../raw-receiver.ts";

export interface KenloRawPayload {
  codigo?: string | number | null | undefined;
  tipo?: string | null | undefined;
  finalidade?: string | null | undefined;
  status?: string | null | undefined;
  precoVenda?: string | number | null | undefined;
  precoLocacao?: string | number | null | undefined;
  valorCondominio?: string | number | null | undefined;
  valorIptu?: string | number | null | undefined;
  areaUtil?: string | number | null | undefined;
  areaTotal?: string | number | null | undefined;
  areaTerreno?: string | number | null | undefined;
  quartos?: string | number | null | undefined;
  suites?: string | number | null | undefined;
  banheiros?: string | number | null | undefined;
  vagas?: string | number | null | undefined;
  unidade?: string | number | null | undefined;
  andar?: string | number | null | undefined;
  torre?: string | null | undefined;
  matricula?: string | null | undefined;
  titulo?: string | null | undefined;
  descricao?: string | null | undefined;
  endereco?: {
    logradouro?: string | null | undefined;
    numero?: string | number | null | undefined;
    complemento?: string | null | undefined;
    bairro?: string | null | undefined;
    cidade?: string | null | undefined;
    estado?: string | null | undefined;
    cep?: string | null | undefined;
    latitude?: number | string | null | undefined;
    longitude?: number | string | null | undefined;
  } | null | undefined;
  fotos?: Array<{
    url?: string | null | undefined;
    principal?: boolean | null | undefined;
    ordem?: number | null | undefined;
    descricao?: string | null | undefined;
  }> | null | undefined;
  caracteristicas?: string[] | null | undefined;
  exclusivo?: boolean | null | undefined;
  [key: string]: unknown;
}

export interface KenloMappedResult {
  unit: Unit;
  property: Property;
  media_assets: MediaAsset[];
  raw_receipt: ReturnType<typeof RawReceiver.receive>;
}

export function mapKenloPropertyType(tipo?: string | null | undefined): PropertyType {
  if (!tipo) return "apartment";
  const clean = tipo.toLowerCase().trim();
  if (clean.includes("cobertura")) return "penthouse";
  if (clean.includes("casa em condominio") || clean.includes("casa de condominio")) return "house_condo";
  if (clean.includes("casa")) return "house";
  if (clean.includes("studio")) return "studio";
  if (clean.includes("loft")) return "loft";
  if (clean.includes("flat")) return "flat";
  if (clean.includes("terreno") || clean.includes("lote")) return "land";
  if (clean.includes("fazenda") || clean.includes("sitio") || clean.includes("chacara")) return "farm";
  if (clean.includes("sala") || clean.includes("conjunto")) return "commercial_room";
  if (clean.includes("predio") || clean.includes("edificio")) return "whole_building";
  if (clean.includes("galpao") || clean.includes("deposito")) return "warehouse";
  return "apartment";
}

export function mapKenloTransactionType(finalidade?: string | null | undefined): TransactionType {
  if (!finalidade) return "sale";
  const clean = finalidade.toLowerCase().trim();
  if (clean.includes("loca") && clean.includes("venda")) return "sale_rent";
  if (clean.includes("loca") || clean.includes("aluguel")) return "rent";
  if (clean.includes("temporada")) return "season_rent";
  return "sale";
}

export function mapKenloStatus(status?: string | null | undefined): PropertyStatus {
  if (!status) return "available";
  const clean = status.toLowerCase().trim();
  if (clean.includes("inativo") || clean.includes("desativado")) return "suspended";
  if (clean.includes("vendido")) return "sold";
  if (clean.includes("alugado") || clean.includes("locado")) return "rented";
  if (clean.includes("reservado")) return "reserved";
  if (clean.includes("proposta")) return "under_offer";
  if (clean.includes("rascunho")) return "draft";
  return "available";
}

export class KenloMapper {
  /**
   * Mapeia payload bruto vindo da Kenlo (Webhook ou API) para as entidades canônicas PIBRAS.
   */
  public static map(raw: KenloRawPayload, options?: { batch_id?: string; tenant_id?: string }): KenloMappedResult {
    const rawCode = raw.codigo != null ? String(raw.codigo).trim() : null;
    const receipt = RawReceiver.receive({
      source_system: "kenlo",
      source_record_id: rawCode ?? undefined,
      payload: raw as Record<string, unknown>,
      sync_batch_id: options?.batch_id,
    });

    const now = new Date().toISOString();
    const unitId = randomUUID();
    const propertyId = randomUUID();

    const end = raw.endereco || {};
    const street = end.logradouro ?? null;
    const number = end.numero != null ? String(end.numero) : null;
    const complement = end.complemento ?? null;
    const neighborhood = end.bairro ?? null;
    const city = end.cidade ?? "São Paulo";
    const state = (end.estado ?? "SP").toUpperCase().slice(0, 2);
    const cep = end.cep ? String(end.cep).replace(/\D/g, "") : null;

    const lat = end.latitude != null ? Number(end.latitude) : null;
    const lng = end.longitude != null ? Number(end.longitude) : null;

    const address: Address = {
      street,
      number,
      complement,
      neighborhood_id: null,
      neighborhood_raw: neighborhood,
      city,
      state,
      postal_code: cep,
      country: "BR",
      latitude: lat && !isNaN(lat) ? lat : null,
      longitude: lng && !isNaN(lng) ? lng : null,
      formatted: `${street || ""}, ${number || "s/n"} - ${neighborhood || ""}, ${city}/${state}`.trim(),
    };

    const usableArea = parseAreaM2(raw.areaUtil);
    const totalArea = parseAreaM2(raw.areaTotal);
    const lotArea = parseAreaM2(raw.areaTerreno);
    const bedrooms = parseInteger(raw.quartos);
    const suites = parseInteger(raw.suites);
    const bathrooms = parseInteger(raw.banheiros);
    const parking = parseInteger(raw.vagas);

    const askingPrice = parseBRLToCentavos(raw.precoVenda);
    const rentPrice = parseBRLToCentavos(raw.precoLocacao);
    const condoFee = parseBRLToCentavos(raw.valorCondominio);
    const iptuAnnual = parseBRLToCentavos(raw.valorIptu);

    const propType = mapKenloPropertyType(raw.tipo);
    const transType = mapKenloTransactionType(raw.finalidade);
    const propStatus = mapKenloStatus(raw.status);

    const tower = raw.torre ?? null;
    const unitNum = raw.unidade != null ? String(raw.unidade) : null;
    const floor = parseInteger(raw.andar);
    const matricula = raw.matricula ?? null;

    const dedupeKey = buildUnitDedupeKey({
      matricula,
      address,
      tower,
      floor,
      unit_number: unitNum,
    });
    const addrKey = buildNormalizedAddressKey(address);
    const areaSig = buildAreaSignature({
      usable_area_m2: usableArea ?? null,
      bedrooms: bedrooms ?? null,
      suites: suites ?? null,
      parking_spaces: parking ?? null,
    });

    const audit: AuditStamp = {
      created_at: now,
      updated_at: now,
      created_by: "kenlo_connector",
      updated_by: null,
      version: 1,
      record_state: "draft",
      completeness_score: usableArea && askingPrice && neighborhood ? 90 : 60,
    };

    const unit: Unit = {
      id: unitId,
      building_id: null,
      matricula,
      dedupe_key: dedupeKey,
      normalized_address_key: addrKey,
      area_signature: areaSig,
      duplicate_of_unit_id: null,
      dedupe_confidence: null,
      dedupe_review_state: "unreviewed",
      property_type: propType,
      address,
      unit_number: unitNum,
      tower,
      floor: floor ?? null,
      usable_area_m2: usableArea ?? null,
      total_area_m2: totalArea ?? null,
      lot_area_m2: lotArea ?? null,
      bedrooms: bedrooms ?? null,
      suites: suites ?? null,
      bathrooms: bathrooms ?? null,
      parking_spaces: parking ?? null,
      features: raw.caracteristicas ?? [],
      condo_fee: condoFee,
      iptu_annual: iptuAnnual,
      provenance: receipt.provenance,
      audit,
    };

    const externalIds = rawCode
      ? [{ namespace: "kenlo", key: "codigo", value: rawCode }]
      : [];

    const property: Property = {
      id: propertyId,
      code: rawCode,
      external_ids: externalIds,
      unit_id: unitId,
      building_id: null,
      transaction_type: transType,
      property_status: propStatus,
      availability: "available",
      asking_price: askingPrice,
      rent_price: rentPrice,
      min_accepted_price: undefined,
      exclusive: Boolean(raw.exclusivo),
      exclusivity_until: null,
      headline: raw.titulo ?? `${raw.tipo || "Imóvel"} em ${neighborhood || city}`,
      summary: raw.descricao ?? null,
      primary_broker_id: null,
      published: propStatus === "available",
      last_price_change_at: null,
      owners: [],
      brokers: [],
      provenance: receipt.provenance,
      audit,
    };

    // Mapear fotos para MediaAsset
    const mediaAssets: MediaAsset[] = (raw.fotos || [])
      .filter((f) => f.url && f.url.startsWith("http"))
      .map((f, idx) => ({
        id: randomUUID(),
        scope: "property",
        property_id: propertyId,
        unit_id: unitId,
        building_id: null,
        media_type: "photo",
        media_role: f.principal || idx === 0 ? "cover" : "gallery",
        url: f.url as string,
        storage_key: null,
        width: null,
        height: null,
        duration_s: null,
        order_index: f.ordem ?? idx,
        caption: f.descricao ?? null,
        media_rights: "licensed",
        visibility: "public",
        is_cover: Boolean(f.principal || idx === 0),
        checksum: null,
        ai_tags: [],
        provenance: receipt.provenance,
        audit,
      }));

    return {
      unit,
      property,
      media_assets: mediaAssets,
      raw_receipt: receipt,
    };
  }
}
