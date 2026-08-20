import type { Address } from "../../types/mbras.ts";

const STREET_TYPE_MAP: Record<string, string> = {
  r: "rua",
  rua: "rua",
  av: "avenida",
  ave: "avenida",
  avenida: "avenida",
  al: "alameda",
  alameda: "alameda",
  pca: "praca",
  pça: "praca",
  praca: "praca",
  praça: "praca",
  tr: "travessa",
  travessa: "travessa",
  rod: "rodovia",
  rodovia: "rodovia",
  est: "estrada",
  estrada: "estrada",
  lgo: "largo",
  largo: "largo",
};

const NEIGHBORHOOD_ALIASES: Record<string, string> = {
  "jd europa": "jardim europa",
  "jd. europa": "jardim europa",
  "jardim europa": "jardim europa",
  "jd paulista": "jardim paulista",
  "jd. paulista": "jardim paulista",
  "jardim paulista": "jardim paulista",
  "jd paulistano": "jardim paulistano",
  "jd. paulistano": "jardim paulistano",
  "jardim paulistano": "jardim paulistano",
  "v nova conceicao": "vila nova conceicao",
  "v. nova conceicao": "vila nova conceicao",
  "vl nova conceicao": "vila nova conceicao",
  "vl. nova conceicao": "vila nova conceicao",
  "vila nova conceicao": "vila nova conceicao",
  "itaim": "itaim bibi",
  "itaim bibi": "itaim bibi",
  "higienopolis": "higienopolis",
  "moema passaros": "moema",
  "moema indios": "moema",
  "morumbi": "morumbi",
  "cidade jardim": "cidade jardim",
  "pinheiros": "pinheiros",
  "alto de pinheiros": "alto de pinheiros",
};

/**
 * Remove acentos e normaliza para minúsculas e espaços únicos.
 */
export function sanitizeString(val?: string | null | undefined): string {
  if (!val) return "";
  return val
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^\w\s]/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/**
 * Normaliza prefixo de logradouro (Rua, Av, etc.).
 */
export function normalizeStreetName(street?: string | null | undefined): string {
  const clean = sanitizeString(street);
  if (!clean) return "";

  const parts = clean.split(" ");
  const firstWord = parts[0];
  if (firstWord && STREET_TYPE_MAP[firstWord]) {
    parts[0] = STREET_TYPE_MAP[firstWord] ?? firstWord;
  }
  return parts.join(" ");
}

/**
 * Normaliza nome de bairro usando dicionário de sinônimos/apelidos.
 */
export function normalizeNeighborhood(neighborhood?: string | null | undefined): string {
  const clean = sanitizeString(neighborhood);
  if (!clean) return "";
  return NEIGHBORHOOD_ALIASES[clean] ?? clean;
}

/**
 * Normaliza CEP para formato canônico de 8 dígitos numéricos.
 */
export function normalizePostalCode(cep?: string | null | undefined): string {
  if (!cep) return "";
  const digits = cep.replace(/\D/g, "");
  return digits.length === 8 ? digits : "";
}

/**
 * Gera a chave normalizada de endereço:
 * ex: "br:sp:sao_paulo:itaim_bibi:rua_leopoldo_couto_magalhaes_junior:1200"
 */
export function buildNormalizedAddressKey(addr?: Address | null | undefined): string {
  if (!addr) return "";
  const country = sanitizeString(addr.country || "BR");
  const state = sanitizeString(addr.state || "SP");
  const city = sanitizeString(addr.city || "sao paulo").replace(/\s+/g, "_");
  const neighborhood = normalizeNeighborhood(addr.neighborhood_raw).replace(/\s+/g, "_");
  const street = normalizeStreetName(addr.street).replace(/\s+/g, "_");
  const num = sanitizeString(addr.number) || "sn";

  return `${country}:${state}:${city}:${neighborhood}:${street}:${num}`;
}

/**
 * Gera a chave canônica determinística de deduplicação física para Unit:
 * Se matricula existir: "mat:<matricula_normalizada>"
 * Senão: "unit:<addr_key>:t:<tower>:f:<floor>:u:<unit_number>"
 */
export function buildUnitDedupeKey(params: {
  matricula?: string | null | undefined;
  address?: Address | null | undefined;
  tower?: string | null | undefined;
  floor?: number | null | undefined;
  unit_number?: string | null | undefined;
}): string {
  if (params.matricula && params.matricula.trim()) {
    const cleanMatricula = params.matricula.replace(/\D/g, "");
    if (cleanMatricula) {
      return `mat:${cleanMatricula}`;
    }
  }

  const addrKey = buildNormalizedAddressKey(params.address);
  const tower = sanitizeString(params.tower) || "na";
  const floor = params.floor != null ? String(params.floor) : "na";
  const unit = sanitizeString(params.unit_number) || "na";

  return `unit:${addrKey}:t:${tower}:f:${floor}:u:${unit}`;
}

/**
 * Gera uma assinatura de área e características físicas para busca de similaridade (Fuzzy Match).
 */
export function buildAreaSignature(params: {
  usable_area_m2?: number | null | undefined;
  bedrooms?: number | null | undefined;
  suites?: number | null | undefined;
  parking_spaces?: number | null | undefined;
}): string {
  const area = params.usable_area_m2 ? Math.round(params.usable_area_m2) : 0;
  const beds = params.bedrooms ?? 0;
  const suites = params.suites ?? 0;
  const parking = params.parking_spaces ?? 0;
  return `a:${area}_b:${beds}_s:${suites}_p:${parking}`;
}
