import type { Unit, DedupeReviewState } from "../../types/mbras.ts";
import { buildUnitDedupeKey, buildNormalizedAddressKey } from "./normalizer.ts";
import { hammingDistance } from "../media/phash.ts";

export interface MatchResult {
  candidate_unit_id: string | null;
  confidence: number;
  review_state: DedupeReviewState;
  match_reasons: string[];
}

export interface UnitMatchCandidate {
  id: string;
  matricula?: string | null | undefined;
  dedupe_key?: string | null | undefined;
  normalized_address_key?: string | null | undefined;
  usable_area_m2?: number | null | undefined;
  bedrooms?: number | null | undefined;
  suites?: number | null | undefined;
  parking_spaces?: number | null | undefined;
  unit_number?: string | null | undefined;
  /** IPTU anual em centavos para comparação numérica. */
  iptu_annual_amount?: number | null | undefined;
  /** Taxa de condomínio em centavos para comparação numérica. */
  condo_fee_amount?: number | null | undefined;
  /** Checksums pHash das fotos associadas para deduplicação visual. */
  media_checksums?: string[] | null | undefined;
}

export class UnitMatcher {
  /**
   * Avalia uma unidade candidata contra uma lista de unidades existentes no inventário.
   */
  public static match(
    incoming: Unit,
    existingInventory: UnitMatchCandidate[]
  ): MatchResult {
    const incomingDedupeKey =
      incoming.dedupe_key ??
      buildUnitDedupeKey({
        matricula: incoming.matricula,
        address: incoming.address,
        tower: incoming.tower,
        floor: incoming.floor,
        unit_number: incoming.unit_number,
      });

    const incomingAddrKey =
      incoming.normalized_address_key ?? buildNormalizedAddressKey(incoming.address);

    let bestCandidate: UnitMatchCandidate | undefined;
    let highestScore = 0;
    let bestReasons: string[] = [];

    for (const existing of existingInventory) {
      let score = 0;
      const reasons: string[] = [];

      // 1. Matrícula idêntica = certeza absoluta (100%)
      if (
        incoming.matricula &&
        existing.matricula &&
        incoming.matricula.replace(/\D/g, "") === existing.matricula.replace(/\D/g, "")
      ) {
        return {
          candidate_unit_id: existing.id,
          confidence: 1.0,
          review_state: "auto_matched",
          match_reasons: ["Exact matricula match"],
        };
      }

      // 2. Chave determinística dedupe_key idêntica (98%)
      if (existing.dedupe_key && existing.dedupe_key === incomingDedupeKey) {
        return {
          candidate_unit_id: existing.id,
          confidence: 0.98,
          review_state: "auto_matched",
          match_reasons: ["Exact deterministic dedupe_key match"],
        };
      }

      // 3. Heurística: Endereço normalizado igual
      if (
        incomingAddrKey &&
        existing.normalized_address_key &&
        incomingAddrKey === existing.normalized_address_key
      ) {
        score += 0.5;
        reasons.push("Normalized address match (+0.50)");

        // Número da unidade igual
        if (
          incoming.unit_number &&
          existing.unit_number &&
          incoming.unit_number.toLowerCase().trim() === existing.unit_number.toLowerCase().trim()
        ) {
          score += 0.35;
          reasons.push("Unit number match (+0.35)");
        }
      }

      // 4. Comparação de metragem privativa (tolerância de 2%)
      if (incoming.usable_area_m2 && existing.usable_area_m2) {
        const areaDiff = Math.abs(incoming.usable_area_m2 - existing.usable_area_m2);
        const areaPctDiff = areaDiff / existing.usable_area_m2;
        if (areaPctDiff <= 0.02) {
          score += 0.15;
          reasons.push(`Usable area within 2% diff (+0.15)`);
        } else if (areaPctDiff <= 0.05) {
          score += 0.08;
          reasons.push(`Usable area within 5% diff (+0.08)`);
        }
      }

      // 5. Comparação de vagas e dormitórios
      if (
        incoming.bedrooms != null &&
        existing.bedrooms != null &&
        incoming.bedrooms === existing.bedrooms
      ) {
        score += 0.05;
        reasons.push("Bedrooms match (+0.05)");
      }
      if (
        incoming.parking_spaces != null &&
        existing.parking_spaces != null &&
        incoming.parking_spaces === existing.parking_spaces
      ) {
        score += 0.05;
        reasons.push("Parking spaces match (+0.05)");
      }

      // 6. IPTU anual (±5%)
      const incomingIptu = incoming.iptu_annual?.amount;
      const existingIptu = existing.iptu_annual_amount;
      if (incomingIptu && existingIptu) {
        const iptuDiff = Math.abs(incomingIptu - existingIptu) / existingIptu;
        if (iptuDiff <= 0.05) {
          score += 0.05;
          reasons.push("IPTU annual within 5% (+0.05)");
        }
      }

      // 7. Condomínio mensal (±5%)
      const incomingCondo = incoming.condo_fee?.amount;
      const existingCondo = existing.condo_fee_amount;
      if (incomingCondo && existingCondo) {
        const condoDiff = Math.abs(incomingCondo - existingCondo) / existingCondo;
        if (condoDiff <= 0.05) {
          score += 0.05;
          reasons.push("Condo fee within 5% (+0.05)");
        }
      }

      // 8. pHash: deduplicação visual de fotos (Hamming distance ≤ 8)
      const incomingHashes = (incoming as unknown as UnitMatchCandidate).media_checksums;
      const existingHashes = existing.media_checksums;
      if (incomingHashes?.length && existingHashes?.length) {
        const visualMatch = incomingHashes.some((h1) =>
          existingHashes.some((h2) => hammingDistance(h1, h2) <= 8)
        );
        if (visualMatch) {
          score += 0.10;
          reasons.push("Visual media match via pHash (+0.10)");
        }
      }

      if (score > highestScore) {
        highestScore = score;
        bestCandidate = existing;
        bestReasons = reasons;
      }
    }

    // Normalização final do score para o intervalo [0, 1]
    const finalConfidence = Math.min(1.0, Number(highestScore.toFixed(2)));

    let reviewState: DedupeReviewState = "confirmed_unique";
    if (finalConfidence >= 0.95) {
      reviewState = "auto_matched";
    } else if (finalConfidence >= 0.75) {
      reviewState = "needs_review";
    }

    return {
      candidate_unit_id: bestCandidate?.id ?? null,
      confidence: finalConfidence,
      review_state: reviewState,
      match_reasons: bestReasons,
    };
  }
}
