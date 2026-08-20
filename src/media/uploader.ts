import { randomUUID, createHash } from "node:crypto";
import type { SourceSystem, AuditStamp, Provenance, MediaAsset } from "../../types/mbras.ts";

export type StorageProvider = "r2" | "s3" | "local";

export interface UploadRequest {
  file_buffer: Buffer;
  original_filename: string;
  content_type: string;
  scope: "property" | "unit" | "building";
  entity_id: string;
  building_id?: string | null | undefined;
  media_type?: MediaAsset["media_type"] | undefined;
  media_role?: MediaAsset["media_role"] | undefined;
  order_index?: number | undefined;
  caption?: string | null | undefined;
  provenance: Provenance;
}

export interface UploadResult {
  media_asset: MediaAsset;
  storage_key: string;
  checksum_sha256: string;
  size_bytes: number;
}

/**
 * Gera storage_key estruturado para organização determinística no object storage:
 * {scope}/{entity_id}/{uuid}.{ext}
 * Ex: property/a1b2c3d4/9f8e7d6c.jpg
 */
export function buildStorageKey(params: {
  scope: string;
  entity_id: string;
  filename: string;
}): string {
  const ext = params.filename.split(".").pop()?.toLowerCase() ?? "bin";
  const fileId = randomUUID().slice(0, 8);
  return `${params.scope}/${params.entity_id}/${fileId}.${ext}`;
}

/**
 * Extrai extensão normalizada do content-type MIME.
 */
export function mimeToExtension(contentType: string): string {
  const map: Record<string, string> = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
    "image/avif": "avif",
    "image/heic": "heic",
    "image/heif": "heif",
    "image/gif": "gif",
    "image/tiff": "tiff",
    "video/mp4": "mp4",
    "video/quicktime": "mov",
    "video/webm": "webm",
    "application/pdf": "pdf",
  };
  return map[contentType.toLowerCase()] ?? "bin";
}

/**
 * Detecta media_type PIBRAS a partir do content-type MIME.
 */
export function detectMediaType(contentType: string): MediaAsset["media_type"] {
  if (contentType.startsWith("image/")) return "photo";
  if (contentType.startsWith("video/")) return "video";
  if (contentType === "application/pdf") return "document";
  return "photo";
}

export class MediaUploader {
  /**
   * Processa um upload de mídia: calcula checksum, gera storage_key, e retorna
   * um MediaAsset pronto para persistência. O upload efetivo para S3/R2 é
   * responsabilidade do caller (este módulo é storage-agnostic).
   */
  public static processUpload(request: UploadRequest): UploadResult {
    const now = new Date().toISOString();
    const mediaAssetId = randomUUID();

    // SHA-256 do conteúdo binário para deduplicação de mídia idêntica
    const checksumSha256 = createHash("sha256").update(request.file_buffer).digest("hex");
    const sizeBytes = request.file_buffer.length;

    const ext = mimeToExtension(request.content_type);
    const storageKey = buildStorageKey({
      scope: request.scope,
      entity_id: request.entity_id,
      filename: `upload.${ext}`,
    });

    const mediaType = request.media_type ?? detectMediaType(request.content_type);

    const audit: AuditStamp = {
      created_at: now,
      updated_at: now,
      created_by: "media_uploader",
      updated_by: null,
      version: 1,
      record_state: "draft",
    };

    const mediaAsset: MediaAsset = {
      id: mediaAssetId,
      scope: request.scope,
      property_id: request.scope === "property" ? request.entity_id : null,
      unit_id: request.scope === "unit" ? request.entity_id : null,
      building_id: request.building_id ?? null,
      media_type: mediaType,
      media_role: request.media_role ?? "gallery",
      url: `https://media.mbras.com.br/${storageKey}`,
      storage_key: storageKey,
      width: null,
      height: null,
      duration_s: null,
      order_index: request.order_index ?? 0,
      caption: request.caption ?? null,
      media_rights: "owned",
      visibility: "public",
      is_cover: request.media_role === "cover",
      checksum: checksumSha256,
      ai_tags: [],
      provenance: request.provenance,
      audit,
    };

    return {
      media_asset: mediaAsset,
      storage_key: storageKey,
      checksum_sha256: checksumSha256,
      size_bytes: sizeBytes,
    };
  }

  /**
   * Detecta uploads duplicados comparando SHA-256 checksums.
   * Retorna o ID do asset existente se for uma duplicata exata.
   */
  public static findExactDuplicate(
    checksumSha256: string,
    existingAssets: Array<{ id: string; checksum: string | null }>
  ): string | null {
    const match = existingAssets.find((a) => a.checksum === checksumSha256);
    return match ? match.id : null;
  }
}
