/**
 * Perceptual Hash (pHash) para deduplicação visual de imagens.
 * 
 * Implementação simplificada usando Average Hash (aHash) como proxy
 * para uso sem dependências externas. Em produção, substituir por
 * uma implementação DCT-based (phash) via sharp/imagehash.
 *
 * O hash é armazenado em `media_asset.checksum` e usado pelo
 * UnitMatcher para detectar duplicatas com fotos cropadas,
 * watermarkadas ou redimensionadas.
 */

/**
 * Calcula a distância de Hamming entre dois hashes hexadecimais.
 * Retorna o número de bits diferentes (menor = mais similar).
 * Threshold recomendado: ≤ 8 para "mesma foto".
 */
export function hammingDistance(hash1: string, hash2: string): number {
  if (hash1.length !== hash2.length) {
    return Math.max(hash1.length, hash2.length) * 4; // Penalização máxima
  }

  let distance = 0;
  for (let i = 0; i < hash1.length; i++) {
    const xor = parseInt(hash1[i]!, 16) ^ parseInt(hash2[i]!, 16);
    // Brian Kernighan's bit counting
    let bits = xor;
    while (bits) {
      bits &= bits - 1;
      distance++;
    }
  }
  return distance;
}

/**
 * Verifica se dois hashes representam a mesma imagem visual.
 * Threshold padrão: Hamming distance ≤ 8 (64-bit hash).
 */
export function isVisualMatch(hash1: string, hash2: string, threshold = 8): boolean {
  return hammingDistance(hash1, hash2) <= threshold;
}

export interface PHashMatchResult {
  is_match: boolean;
  distance: number;
  threshold: number;
  hash_a: string;
  hash_b: string;
}

/**
 * Compara dois conjuntos de hashes (ex: todas as fotos de dois imóveis).
 * Retorna o melhor match (menor distância).
 */
export function findBestVisualMatch(
  hashesA: string[],
  hashesB: string[],
  threshold = 8
): PHashMatchResult | null {
  if (hashesA.length === 0 || hashesB.length === 0) return null;

  let bestMatch: PHashMatchResult | null = null;

  for (const ha of hashesA) {
    for (const hb of hashesB) {
      const dist = hammingDistance(ha, hb);
      if (!bestMatch || dist < bestMatch.distance) {
        bestMatch = {
          is_match: dist <= threshold,
          distance: dist,
          threshold,
          hash_a: ha,
          hash_b: hb,
        };
      }
    }
  }

  return bestMatch;
}

/**
 * Calcula um hash perceptual simplificado (Average Hash) a partir de
 * dados de luminância brutos. Em produção, usar a implementação
 * DCT do sharp ou phash-image.
 *
 * Entrada: array de valores de luminância (0-255) de uma imagem
 * redimensionada para 8x8 (64 pixels).
 *
 * Saída: hash hexadecimal de 16 caracteres (64 bits).
 */
export function computeAverageHash(luminanceValues: number[]): string {
  if (luminanceValues.length !== 64) {
    throw new Error(`Expected 64 luminance values (8x8), got ${luminanceValues.length}`);
  }

  const mean = luminanceValues.reduce((sum, v) => sum + v, 0) / 64;
  let hashBits = "";
  for (const v of luminanceValues) {
    hashBits += v >= mean ? "1" : "0";
  }

  // Convert 64-bit binary string to 16-char hex
  let hex = "";
  for (let i = 0; i < 64; i += 4) {
    const nibble = hashBits.slice(i, i + 4);
    hex += parseInt(nibble, 2).toString(16);
  }

  return hex;
}
