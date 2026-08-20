import { randomUUID } from "node:crypto";

export type ProcessingJobType = "resize" | "convert_webp" | "convert_avif" | "watermark" | "phash" | "compress_video" | "extract_metadata";
export type ProcessingJobStatus = "pending" | "processing" | "completed" | "failed";

export interface ProcessingJob {
  id: string;
  media_asset_id: string;
  storage_key: string;
  job_type: ProcessingJobType;
  status: ProcessingJobStatus;
  params: ProcessingParams;
  result: ProcessingResult | null;
  error: string | null;
  attempts: number;
  max_attempts: number;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface ProcessingParams {
  /** Target width for resize operations. */
  target_width?: number | undefined;
  /** Target height for resize operations. */
  target_height?: number | undefined;
  /** Quality (1-100) for compression. */
  quality?: number | undefined;
  /** Watermark text overlay. */
  watermark_text?: string | undefined;
  /** Watermark position. */
  watermark_position?: "bottom-right" | "bottom-left" | "center" | "tiled" | undefined;
  /** Watermark opacity (0.0 - 1.0). */
  watermark_opacity?: number | undefined;
  /** Output format. */
  output_format?: string | undefined;
}

export interface ProcessingResult {
  output_storage_key: string;
  output_url: string;
  width?: number | undefined;
  height?: number | undefined;
  size_bytes?: number | undefined;
  phash?: string | undefined;
  metadata?: Record<string, unknown> | undefined;
}

export interface MediaVariant {
  variant_name: string;
  storage_key: string;
  url: string;
  width: number;
  height: number;
  format: string;
  size_bytes: number;
}

/**
 * Definições de variantes padrão PIBRAS para processamento de imagens.
 */
export const MEDIA_VARIANTS = {
  thumbnail: { width: 400, height: 300, quality: 80, format: "webp" },
  gallery: { width: 1200, height: 900, quality: 85, format: "webp" },
  full: { width: 2400, height: 1800, quality: 90, format: "webp" },
  original: { width: 0, height: 0, quality: 100, format: "preserve" },
} as const;

/**
 * Configuração de watermark por canal de distribuição.
 *
 * `text` usa OPERATOR_BRAND, resolvido em tempo de execução a partir do
 * ambiente. O padrão é neutro: nenhuma marca de patrocinador fica embutida.
 */
/**
 * Marca do operador aplicada às imagens.
 *
 * Lida de PIBRAS_OPERATOR_BRAND em tempo de execução. O padrão "PIBRAS" é
 * neutro: nenhum patrocinador fica embutido no código do padrão, e cada
 * operador define a própria marca sem editar o fonte.
 */
export const OPERATOR_BRAND = process.env["PIBRAS_OPERATOR_BRAND"] ?? "PIBRAS";

export const WATERMARK_PROFILES = {
  portal: {
    text: OPERATOR_BRAND,
    position: "bottom-right" as const,
    opacity: 0.35,
  },
  website: {
    text: OPERATOR_BRAND,
    position: "bottom-right" as const,
    opacity: 0.25,
  },
  off_market_pdf: {
    text: `CONFIDENCIAL • ${OPERATOR_BRAND}`,
    position: "tiled" as const,
    opacity: 0.12,
  },
  crm: null, // Sem watermark para uso interno
  broker_network: null,
} as const;

export class MediaProcessor {
  /**
   * Cria o pipeline de processamento completo para uma imagem recém-uploadeada.
   * Gera jobs para: thumbnail, gallery, full (WebP), pHash e metadados.
   */
  public static createImagePipeline(params: {
    media_asset_id: string;
    storage_key: string;
    include_phash?: boolean;
  }): ProcessingJob[] {
    const now = new Date().toISOString();
    const jobs: ProcessingJob[] = [];

    // 1. Thumbnail (400x300 WebP)
    jobs.push(
      MediaProcessor.createJob({
        media_asset_id: params.media_asset_id,
        storage_key: params.storage_key,
        job_type: "resize",
        params: {
          target_width: MEDIA_VARIANTS.thumbnail.width,
          target_height: MEDIA_VARIANTS.thumbnail.height,
          quality: MEDIA_VARIANTS.thumbnail.quality,
          output_format: MEDIA_VARIANTS.thumbnail.format,
        },
        created_at: now,
      })
    );

    // 2. Gallery (1200x900 WebP)
    jobs.push(
      MediaProcessor.createJob({
        media_asset_id: params.media_asset_id,
        storage_key: params.storage_key,
        job_type: "resize",
        params: {
          target_width: MEDIA_VARIANTS.gallery.width,
          target_height: MEDIA_VARIANTS.gallery.height,
          quality: MEDIA_VARIANTS.gallery.quality,
          output_format: MEDIA_VARIANTS.gallery.format,
        },
        created_at: now,
      })
    );

    // 3. Full-size WebP
    jobs.push(
      MediaProcessor.createJob({
        media_asset_id: params.media_asset_id,
        storage_key: params.storage_key,
        job_type: "convert_webp",
        params: {
          quality: MEDIA_VARIANTS.full.quality,
          output_format: "webp",
        },
        created_at: now,
      })
    );

    // 4. pHash para deduplicação visual
    if (params.include_phash !== false) {
      jobs.push(
        MediaProcessor.createJob({
          media_asset_id: params.media_asset_id,
          storage_key: params.storage_key,
          job_type: "phash",
          params: {},
          created_at: now,
        })
      );
    }

    // 5. Extração de metadados (EXIF, GPS, câmera)
    jobs.push(
      MediaProcessor.createJob({
        media_asset_id: params.media_asset_id,
        storage_key: params.storage_key,
        job_type: "extract_metadata",
        params: {},
        created_at: now,
      })
    );

    return jobs;
  }

  /**
   * Cria o pipeline de watermark para uma imagem em um canal específico.
   */
  public static createWatermarkJob(params: {
    media_asset_id: string;
    storage_key: string;
    channel: keyof typeof WATERMARK_PROFILES;
  }): ProcessingJob | null {
    const profile = WATERMARK_PROFILES[params.channel];
    if (!profile) return null; // Canal sem watermark (uso interno)

    return MediaProcessor.createJob({
      media_asset_id: params.media_asset_id,
      storage_key: params.storage_key,
      job_type: "watermark",
      params: {
        watermark_text: profile.text,
        watermark_position: profile.position,
        watermark_opacity: profile.opacity,
      },
    });
  }

  /**
   * Registra a conclusão bem-sucedida de um job de processamento.
   */
  public static recordSuccess(job: ProcessingJob, result: ProcessingResult): ProcessingJob {
    return {
      ...job,
      status: "completed",
      result,
      attempts: job.attempts + 1,
      completed_at: new Date().toISOString(),
    };
  }

  /**
   * Registra uma falha no processamento.
   */
  public static recordFailure(job: ProcessingJob, error: string): ProcessingJob {
    const nextAttempts = job.attempts + 1;
    return {
      ...job,
      status: nextAttempts >= job.max_attempts ? "failed" : "pending",
      error,
      attempts: nextAttempts,
    };
  }

  private static createJob(params: {
    media_asset_id: string;
    storage_key: string;
    job_type: ProcessingJobType;
    params: ProcessingParams;
    created_at?: string;
  }): ProcessingJob {
    const now = params.created_at ?? new Date().toISOString();
    return {
      id: randomUUID(),
      media_asset_id: params.media_asset_id,
      storage_key: params.storage_key,
      job_type: params.job_type,
      status: "pending",
      params: params.params,
      result: null,
      error: null,
      attempts: 0,
      max_attempts: 3,
      created_at: now,
      started_at: null,
      completed_at: null,
    };
  }
}
