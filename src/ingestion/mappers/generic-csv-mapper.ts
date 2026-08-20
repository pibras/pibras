import { randomUUID } from "node:crypto";
import type {
  Unit,
  Property,
  Address,
  Money,
  AuditStamp,
} from "../../../types/mbras.ts";
import {
  buildUnitDedupeKey,
  buildNormalizedAddressKey,
  buildAreaSignature,
} from "../../dedupe/normalizer.ts";
import { RawReceiver } from "../raw-receiver.ts";

export interface MappedEntityBundle {
  unit: Unit;
  property: Property;
  raw_receipt: ReturnType<typeof RawReceiver.receive>;
}

/**
 * Converte string ou número monetário brasileiro (BRL) para centavos inteiros.
 * Ex: "R$ 15.000.000,00" -> 1500000000
 * Ex: "15000000" -> 1500000000
 */
export function parseBRLToCentavos(val?: unknown): Money | undefined {
  if (val == null) return undefined;
  if (typeof val === "number") {
    return { amount: Math.round(val * 100), currency: "BRL" };
  }
  if (typeof val !== "string") return undefined;
  const clean = val.replace(/[R$\s]/g, "").trim();
  if (!clean) return undefined;

  if (clean.includes(",")) {
    const withoutDots = clean.replace(/\./g, "");
    const parts = withoutDots.split(",");
    const intPart = parseInt(parts[0] || "0", 10);
    const decPart = parseInt((parts[1] || "00").padEnd(2, "0").slice(0, 2), 10);
    return { amount: intPart * 100 + decPart, currency: "BRL" };
  }

  const num = parseFloat(clean);
  if (isNaN(num)) return undefined;
  return { amount: Math.round(num * 100), currency: "BRL" };
}

/**
 * Converte área para número de m².
 * Ex: "740 m²" -> 740
 */
export function parseAreaM2(val?: unknown): number | undefined {
  if (val == null) return undefined;
  if (typeof val === "number") return val;
  if (typeof val !== "string") return undefined;
  const clean = val.replace(/[m²M2\s]/g, "").replace(/\./g, "").replace(",", ".");
  const num = parseFloat(clean);
  return isNaN(num) ? undefined : num;
}

export function parseInteger(val?: unknown): number | undefined {
  if (val == null) return undefined;
  if (typeof val === "number") return Math.round(val);
  if (typeof val !== "string") return undefined;
  const num = parseInt(val.replace(/\D/g, ""), 10);
  return isNaN(num) ? undefined : num;
}

export class GenericCSVMapper {
  /**
   * Mapeia uma linha bruta de planilha/CSV para o modelo canônico PIBRAS.
   */
  public static mapRow(
    rawRow: Record<string, unknown>,
    options?: {
      source_system?: "csv_import" | "excel_import";
      tenant_id?: string;
      batch_id?: string;
    }
  ): MappedEntityBundle {
    const sourceSystem = options?.source_system ?? "csv_import";
    const receipt = RawReceiver.receive({
      source_system: sourceSystem,
      payload: rawRow,
      sync_batch_id: options?.batch_id,
    });

    const now = new Date().toISOString();
    const unitId = randomUUID();
    const propertyId = randomUUID();

    const street = (rawRow["rua"] ?? rawRow["endereco"] ?? rawRow["logradouro"] ?? rawRow["street"]) as string | undefined;
    const number = (rawRow["numero"] ?? rawRow["num"] ?? rawRow["number"]) as string | number | undefined;
    const complement = (rawRow["complemento"] ?? rawRow["compl"] ?? rawRow["complement"]) as string | undefined;
    const neighborhood = (rawRow["bairro"] ?? rawRow["neighborhood"]) as string | undefined;
    const city = (rawRow["cidade"] ?? rawRow["city"] ?? "São Paulo") as string;
    const state = ((rawRow["estado"] ?? rawRow["uf"] ?? rawRow["state"] ?? "SP") as string).toUpperCase().slice(0, 2);
    const cep = (rawRow["cep"] ?? rawRow["postal_code"]) as string | undefined;

    const address: Address = {
      street: street ?? null,
      number: number != null ? String(number) : null,
      complement: complement ?? null,
      neighborhood_id: null,
      neighborhood_raw: neighborhood ?? null,
      city: city ?? null,
      state: state ?? null,
      postal_code: cep ?? null,
      country: "BR",
      latitude: null,
      longitude: null,
      formatted: `${street || ""}, ${number || "s/n"} - ${neighborhood || ""}, ${city || ""}/${state || ""}`.trim(),
    };

    const matricula = (rawRow["matricula"] ?? rawRow["numero_matricula"]) as string | undefined;
    const tower = (rawRow["torre"] ?? rawRow["bloco"] ?? rawRow["tower"]) as string | undefined;
    const unitNum = (rawRow["unidade"] ?? rawRow["apartamento"] ?? rawRow["apto"] ?? rawRow["unit_number"]) as string | number | undefined;
    const floor = parseInteger(rawRow["andar"] ?? rawRow["floor"]);

    const usableArea = parseAreaM2(rawRow["area_util"] ?? rawRow["area_privativa"] ?? rawRow["metragem"] ?? rawRow["usable_area"]);
    const totalArea = parseAreaM2(rawRow["area_total"] ?? rawRow["total_area"]);
    const bedrooms = parseInteger(rawRow["dormitorios"] ?? rawRow["quartos"] ?? rawRow["bedrooms"]);
    const suites = parseInteger(rawRow["suites"]);
    const bathrooms = parseInteger(rawRow["banheiros"] ?? rawRow["bathrooms"]);
    const parking = parseInteger(rawRow["vagas"] ?? rawRow["garagens"] ?? rawRow["parking_spaces"]);

    const condoFee = parseBRLToCentavos(rawRow["condominio"] ?? rawRow["valor_condominio"]);
    const iptuAnnual = parseBRLToCentavos(rawRow["iptu"] ?? rawRow["iptu_anual"]);
    const askingPrice = parseBRLToCentavos(rawRow["valor"] ?? rawRow["preco_venda"] ?? rawRow["preco"] ?? rawRow["asking_price"]);

    const addrKey = buildNormalizedAddressKey(address);
    const dedupeKey = buildUnitDedupeKey({
      matricula: matricula ?? null,
      address,
      tower: tower ?? null,
      floor: floor ?? null,
      unit_number: unitNum != null ? String(unitNum) : null,
    });
    const areaSig = buildAreaSignature({
      usable_area_m2: usableArea ?? null,
      bedrooms: bedrooms ?? null,
      suites: suites ?? null,
      parking_spaces: parking ?? null,
    });

    const audit: AuditStamp = {
      created_at: now,
      updated_at: now,
      created_by: "csv_mapper",
      updated_by: null,
      version: 1,
      record_state: "draft",
      completeness_score: usableArea && askingPrice && neighborhood ? 85 : 50,
    };

    const unit: Unit = {
      id: unitId,
      building_id: null,
      matricula: matricula ?? null,
      dedupe_key: dedupeKey,
      normalized_address_key: addrKey,
      area_signature: areaSig,
      duplicate_of_unit_id: null,
      dedupe_confidence: null,
      dedupe_review_state: "unreviewed",
      property_type: "apartment",
      address,
      unit_number: unitNum != null ? String(unitNum) : null,
      tower: tower ?? null,
      floor: floor ?? null,
      usable_area_m2: usableArea ?? null,
      total_area_m2: totalArea ?? null,
      lot_area_m2: null,
      bedrooms: bedrooms ?? null,
      suites: suites ?? null,
      bathrooms: bathrooms ?? null,
      parking_spaces: parking ?? null,
      features: [],
      condo_fee: condoFee,
      iptu_annual: iptuAnnual,
      provenance: receipt.provenance,
      audit,
    };

    const property: Property = {
      id: propertyId,
      code: null,
      external_ids: [],
      unit_id: unitId,
      building_id: null,
      transaction_type: "sale",
      property_status: "draft",
      availability: "available",
      asking_price: askingPrice,
      rent_price: undefined,
      min_accepted_price: undefined,
      exclusive: false,
      exclusivity_until: null,
      headline: (rawRow["titulo"] ?? rawRow["headline"] ?? `Apartamento no ${neighborhood || city}`) as string,
      summary: (rawRow["descricao"] ?? rawRow["summary"] ?? rawRow["description"]) as string ?? null,
      primary_broker_id: null,
      published: false,
      last_price_change_at: null,
      owners: [],
      brokers: [],
      provenance: receipt.provenance,
      audit,
    };

    return {
      unit,
      property,
      raw_receipt: receipt,
    };
  }
}
