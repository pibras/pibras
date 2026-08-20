import { randomUUID } from "node:crypto";
import type {
  Unit,
  Property,
  Address,
  MediaAsset,
  PropertyType,
  TransactionType,
  AuditStamp,
} from "../../../types/mbras.ts";
import {
  buildUnitDedupeKey,
  buildNormalizedAddressKey,
  buildAreaSignature,
} from "../../dedupe/normalizer.ts";
import { parseBRLToCentavos, parseAreaM2, parseInteger } from "./generic-csv-mapper.ts";
import { RawReceiver } from "../raw-receiver.ts";

export interface XMLItemParsed {
  code?: string | undefined;
  propertyType?: string | undefined;
  transactionType?: string | undefined;
  title?: string | undefined;
  description?: string | undefined;
  priceSale?: string | undefined;
  priceRent?: string | undefined;
  condoFee?: string | undefined;
  iptuAnnual?: string | undefined;
  usableArea?: string | undefined;
  totalArea?: string | undefined;
  bedrooms?: string | undefined;
  suites?: string | undefined;
  bathrooms?: string | undefined;
  parkingSpaces?: string | undefined;
  street?: string | undefined;
  number?: string | undefined;
  complement?: string | undefined;
  neighborhood?: string | undefined;
  city?: string | undefined;
  state?: string | undefined;
  postalCode?: string | undefined;
  latitude?: string | undefined;
  longitude?: string | undefined;
  photoUrls: string[];
  features: string[];
}

export interface ZapXMLMappedBundle {
  unit: Unit;
  property: Property;
  media_assets: MediaAsset[];
  raw_receipt: ReturnType<typeof RawReceiver.receive>;
}

/**
 * Utilitário leve e resiliente para extrair tags XML sem necessidade de parser externo.
 */
export function extractTagContent(xmlChunk: string, tagName: string): string | undefined {
  const regex = new RegExp(`<${tagName}(?:\\s+[^>]*)?>([\\s\\S]*?)<\\/${tagName}>`, "i");
  const match = xmlChunk.match(regex);
  return match && match[1] ? match[1].trim() : undefined;
}

export function extractAllTagContents(xmlChunk: string, tagName: string): string[] {
  const regex = new RegExp(`<${tagName}(?:\\s+[^>]*)?>([\\s\\S]*?)<\\/${tagName}>`, "gi");
  const results: string[] = [];
  let match;
  while ((match = regex.exec(xmlChunk)) !== null) {
    if (match[1]) results.push(match[1].trim());
  }
  return results;
}

export class ZapXMLMapper {
  /**
   * Extrai blocos individuais de imóveis de um feed XML completo (ZAP, VivaReal, OLX ou PIBRAS).
   */
  public static splitXmlItems(xmlContent: string): string[] {
    const listingItems = extractAllTagContents(xmlContent, "Listing");
    if (listingItems.length > 0) return listingItems;

    const imovelItems = extractAllTagContents(xmlContent, "Imovel");
    if (imovelItems.length > 0) return imovelItems;

    const propertyItems = extractAllTagContents(xmlContent, "Property");
    if (propertyItems.length > 0) return propertyItems;

    return [];
  }

  /**
   * Converte um fragmento XML de um imóvel em dados estruturados.
   */
  public static parseItem(itemXml: string): XMLItemParsed {
    const code =
      extractTagContent(itemXml, "ExternalId") ??
      extractTagContent(itemXml, "CodigoImovel") ??
      extractTagContent(itemXml, "ListingID") ??
      extractTagContent(itemXml, "Code");

    const propertyType =
      extractTagContent(itemXml, "TipoImovel") ??
      extractTagContent(itemXml, "PropertyType") ??
      extractTagContent(itemXml, "Tipo");

    const transactionType =
      extractTagContent(itemXml, "TransactionType") ??
      extractTagContent(itemXml, "Finalidade") ??
      extractTagContent(itemXml, "TipoNegocio");

    const title = extractTagContent(itemXml, "Title") ?? extractTagContent(itemXml, "Titulo");
    const description = extractTagContent(itemXml, "Description") ?? extractTagContent(itemXml, "Descricao");

    const priceSale =
      extractTagContent(itemXml, "PrecoVenda") ??
      extractTagContent(itemXml, "ValorVenda") ??
      extractTagContent(itemXml, "Price") ??
      extractTagContent(itemXml, "ListPrice");

    const priceRent =
      extractTagContent(itemXml, "PrecoLocacao") ??
      extractTagContent(itemXml, "ValorLocacao") ??
      extractTagContent(itemXml, "RentPrice");

    const condoFee =
      extractTagContent(itemXml, "ValorCondominio") ??
      extractTagContent(itemXml, "CondoFee") ??
      extractTagContent(itemXml, "TaxaCondominio");

    const iptuAnnual =
      extractTagContent(itemXml, "ValorIPTU") ??
      extractTagContent(itemXml, "IPTU") ??
      extractTagContent(itemXml, "PropertyTax");

    const usableArea =
      extractTagContent(itemXml, "AreaUtil") ??
      extractTagContent(itemXml, "AreaPrivativa") ??
      extractTagContent(itemXml, "LivingArea");

    const totalArea = extractTagContent(itemXml, "AreaTotal") ?? extractTagContent(itemXml, "TotalArea");

    const bedrooms =
      extractTagContent(itemXml, "QtdDormitorios") ??
      extractTagContent(itemXml, "Bedrooms") ??
      extractTagContent(itemXml, "Quartos");

    const suites = extractTagContent(itemXml, "QtdSuites") ?? extractTagContent(itemXml, "Suites");
    const bathrooms = extractTagContent(itemXml, "QtdBanheiros") ?? extractTagContent(itemXml, "Bathrooms");
    const parkingSpaces =
      extractTagContent(itemXml, "QtdVagas") ??
      extractTagContent(itemXml, "Garage") ??
      extractTagContent(itemXml, "Vagas");

    const street =
      extractTagContent(itemXml, "Logradouro") ??
      extractTagContent(itemXml, "Street") ??
      extractTagContent(itemXml, "Endereco");

    const number = extractTagContent(itemXml, "Numero") ?? extractTagContent(itemXml, "Number");
    const complement = extractTagContent(itemXml, "Complemento") ?? extractTagContent(itemXml, "Complement");
    const neighborhood = extractTagContent(itemXml, "Bairro") ?? extractTagContent(itemXml, "Neighborhood");
    const city = extractTagContent(itemXml, "Cidade") ?? extractTagContent(itemXml, "City") ?? "São Paulo";
    const state = (extractTagContent(itemXml, "Estado") ?? extractTagContent(itemXml, "State") ?? "SP")
      .toUpperCase()
      .slice(0, 2);
    const postalCode = extractTagContent(itemXml, "CEP") ?? extractTagContent(itemXml, "PostalCode");
    const latitude = extractTagContent(itemXml, "Latitude");
    const longitude = extractTagContent(itemXml, "Longitude");

    const photoUrls: string[] = [];
    const fotosBlock = extractTagContent(itemXml, "Fotos") ?? extractTagContent(itemXml, "Media") ?? itemXml;
    const urlMatches = fotosBlock.match(/https?:\/\/[^\s"'<>]+/gi) || [];
    for (const url of urlMatches) {
      if (!photoUrls.includes(url)) photoUrls.push(url);
    }

    const features: string[] = [];
    const itemsBlock = extractTagContent(itemXml, "Caracteristicas") ?? extractTagContent(itemXml, "Features");
    if (itemsBlock) {
      const items = extractAllTagContents(itemsBlock, "Item");
      features.push(...items);
    }

    return {
      code: code ?? undefined,
      propertyType: propertyType ?? undefined,
      transactionType: transactionType ?? undefined,
      title: title ?? undefined,
      description: description ?? undefined,
      priceSale: priceSale ?? undefined,
      priceRent: priceRent ?? undefined,
      condoFee: condoFee ?? undefined,
      iptuAnnual: iptuAnnual ?? undefined,
      usableArea: usableArea ?? undefined,
      totalArea: totalArea ?? undefined,
      bedrooms: bedrooms ?? undefined,
      suites: suites ?? undefined,
      bathrooms: bathrooms ?? undefined,
      parkingSpaces: parkingSpaces ?? undefined,
      street: street ?? undefined,
      number: number ?? undefined,
      complement: complement ?? undefined,
      neighborhood: neighborhood ?? undefined,
      city: city ?? undefined,
      state: state ?? undefined,
      postalCode: postalCode ?? undefined,
      latitude: latitude ?? undefined,
      longitude: longitude ?? undefined,
      photoUrls,
      features,
    };
  }

  /**
   * Mapeia um fragmento XML para as entidades canônicas PIBRAS.
   */
  public static mapXmlItem(itemXml: string, options?: { batch_id?: string; source_system?: "zap_vivareal" | "olx" | "xml_generic" }): ZapXMLMappedBundle {
    const sourceSystem = options?.source_system ?? "zap_vivareal";
    const parsed = this.parseItem(itemXml);

    const receipt = RawReceiver.receive({
      source_system: sourceSystem,
      source_record_id: parsed.code,
      payload: parsed as unknown as Record<string, unknown>,
      sync_batch_id: options?.batch_id,
    });

    const now = new Date().toISOString();
    const unitId = randomUUID();
    const propertyId = randomUUID();

    const lat = parsed.latitude ? Number(parsed.latitude) : null;
    const lng = parsed.longitude ? Number(parsed.longitude) : null;

    const address: Address = {
      street: parsed.street ?? null,
      number: parsed.number ?? null,
      complement: parsed.complement ?? null,
      neighborhood_id: null,
      neighborhood_raw: parsed.neighborhood ?? null,
      city: parsed.city ?? null,
      state: parsed.state ?? null,
      postal_code: parsed.postalCode ? parsed.postalCode.replace(/\D/g, "") : null,
      country: "BR",
      latitude: lat && !isNaN(lat) ? lat : null,
      longitude: lng && !isNaN(lng) ? lng : null,
      formatted: `${parsed.street || ""}, ${parsed.number || "s/n"} - ${parsed.neighborhood || ""}, ${parsed.city || ""}/${parsed.state || ""}`.trim(),
    };

    const usableArea = parseAreaM2(parsed.usableArea);
    const totalArea = parseAreaM2(parsed.totalArea);
    const bedrooms = parseInteger(parsed.bedrooms);
    const suites = parseInteger(parsed.suites);
    const bathrooms = parseInteger(parsed.bathrooms);
    const parking = parseInteger(parsed.parkingSpaces);

    const askingPrice = parseBRLToCentavos(parsed.priceSale);
    const rentPrice = parseBRLToCentavos(parsed.priceRent);
    const condoFee = parseBRLToCentavos(parsed.condoFee);
    const iptuAnnual = parseBRLToCentavos(parsed.iptuAnnual);

    const dedupeKey = buildUnitDedupeKey({
      address,
      unit_number: parsed.number ?? null,
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
      created_by: "zap_xml_connector",
      updated_by: null,
      version: 1,
      record_state: "draft",
      completeness_score: usableArea && askingPrice && parsed.neighborhood ? 85 : 55,
    };

    let pType: PropertyType = "apartment";
    if (parsed.propertyType) {
      const cleanType = parsed.propertyType.toLowerCase();
      if (cleanType.includes("cobertura")) pType = "penthouse";
      else if (cleanType.includes("casa")) pType = "house";
      else if (cleanType.includes("terreno")) pType = "land";
      else if (cleanType.includes("comercial") || cleanType.includes("sala")) pType = "commercial_room";
    }

    let tType: TransactionType = "sale";
    if (parsed.transactionType) {
      const cleanTrans = parsed.transactionType.toLowerCase();
      if (cleanTrans.includes("loca") || cleanTrans.includes("aluguel")) tType = "rent";
    }

    const unit: Unit = {
      id: unitId,
      building_id: null,
      matricula: null,
      dedupe_key: dedupeKey,
      normalized_address_key: addrKey,
      area_signature: areaSig,
      duplicate_of_unit_id: null,
      dedupe_confidence: null,
      dedupe_review_state: "unreviewed",
      property_type: pType,
      address,
      unit_number: parsed.number ?? null,
      tower: null,
      floor: null,
      usable_area_m2: usableArea ?? null,
      total_area_m2: totalArea ?? null,
      lot_area_m2: null,
      bedrooms: bedrooms ?? null,
      suites: suites ?? null,
      bathrooms: bathrooms ?? null,
      parking_spaces: parking ?? null,
      features: parsed.features,
      condo_fee: condoFee,
      iptu_annual: iptuAnnual,
      provenance: receipt.provenance,
      audit,
    };

    const externalIds = parsed.code
      ? [{ namespace: sourceSystem, key: "code", value: parsed.code }]
      : [];

    const property: Property = {
      id: propertyId,
      code: parsed.code ?? null,
      external_ids: externalIds,
      unit_id: unitId,
      building_id: null,
      transaction_type: tType,
      property_status: "available",
      availability: "available",
      asking_price: askingPrice,
      rent_price: rentPrice,
      min_accepted_price: undefined,
      exclusive: false,
      exclusivity_until: null,
      headline: parsed.title ?? `Imóvel em ${parsed.neighborhood || parsed.city || "São Paulo"}`,
      summary: parsed.description ?? null,
      primary_broker_id: null,
      published: true,
      last_price_change_at: null,
      owners: [],
      brokers: [],
      provenance: receipt.provenance,
      audit,
    };

    const mediaAssets: MediaAsset[] = parsed.photoUrls.map((url, idx) => ({
      id: randomUUID(),
      scope: "property",
      property_id: propertyId,
      unit_id: unitId,
      building_id: null,
      media_type: "photo",
      media_role: idx === 0 ? "cover" : "gallery",
      url,
      storage_key: null,
      width: null,
      height: null,
      duration_s: null,
      order_index: idx,
      caption: null,
      media_rights: "licensed",
      visibility: "public",
      is_cover: idx === 0,
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
