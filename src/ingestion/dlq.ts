import { randomUUID } from "node:crypto";
import type { SourceSystem, RecordState } from "../../types/mbras.ts";

export type DLQErrorCode =
  | "SCHEMA_VALIDATION_ERROR"
  | "MAPPING_ERROR"
  | "CORRUPT_PAYLOAD"
  | "NETWORK_OR_TIMEOUT"
  | "RATE_LIMITED"
  | "UNAUTHORIZED"
  | "DUPLICATE_DROP"
  | "UNKNOWN";

export type QuarantineStatus = "quarantined" | "retrying" | "resolved" | "dropped";

export interface DeadLetterRecord {
  id: string;
  source_system: SourceSystem;
  source_record_id: string | null;
  sync_batch_id: string | null;
  raw_payload: Record<string, unknown> | Array<Record<string, unknown>> | string;
  error_code: DLQErrorCode;
  error_message: string;
  error_stack: string | null;
  retry_count: number;
  max_retries: number;
  next_retry_at: string | null;
  status: QuarantineStatus;
  record_state: RecordState;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  resolution_notes: string | null;
}

export interface DLQEnqueueInput {
  source_system: SourceSystem;
  source_record_id?: string | null | undefined;
  sync_batch_id?: string | null | undefined;
  raw_payload: Record<string, unknown> | Array<Record<string, unknown>> | string;
  error_code: DLQErrorCode;
  error: Error | string;
  max_retries?: number | undefined;
}

export class DeadLetterQueue {
  private static readonly DEFAULT_MAX_RETRIES = 5;
  private static readonly BASE_BACKOFF_SECONDS = 30;

  /**
   * Calcula o próximo instante de retry usando backoff exponencial: base * 2^(retry_count)
   */
  public static calculateNextRetry(retryCount: number, baseSeconds = DeadLetterQueue.BASE_BACKOFF_SECONDS): string {
    const delaySeconds = baseSeconds * Math.pow(2, retryCount);
    const nextDate = new Date(Date.now() + delaySeconds * 1000);
    return nextDate.toISOString();
  }

  /**
   * Cria um registro imutável de Dead Letter / Quarentena para um payload que falhou no processamento.
   */
  public static enqueue(input: DLQEnqueueInput): DeadLetterRecord {
    const now = new Date().toISOString();
    const id = randomUUID();
    const maxRetries = input.max_retries ?? DeadLetterQueue.DEFAULT_MAX_RETRIES;
    const errorMessage = typeof input.error === "string" ? input.error : input.error.message;
    const errorStack = typeof input.error === "object" && input.error.stack ? input.error.stack : null;

    const nextRetryAt = maxRetries > 0 ? DeadLetterQueue.calculateNextRetry(0) : null;

    return {
      id,
      source_system: input.source_system,
      source_record_id: input.source_record_id ?? null,
      sync_batch_id: input.sync_batch_id ?? null,
      raw_payload: input.raw_payload,
      error_code: input.error_code,
      error_message: errorMessage,
      error_stack: errorStack,
      retry_count: 0,
      max_retries: maxRetries,
      next_retry_at: nextRetryAt,
      status: "quarantined",
      record_state: "rejected",
      created_at: now,
      updated_at: now,
      resolved_at: null,
      resolution_notes: null,
    };
  }

  /**
   * Processa uma tentativa de retry: incrementa contador ou marca como dropped se exceder max_retries.
   */
  public static recordRetryAttempt(
    record: DeadLetterRecord,
    newError?: Error | string | null
  ): DeadLetterRecord {
    const now = new Date().toISOString();
    const nextCount = record.retry_count + 1;

    if (newError) {
      const errorMessage = typeof newError === "string" ? newError : newError.message;
      const isExhausted = nextCount >= record.max_retries;

      return {
        ...record,
        retry_count: nextCount,
        error_message: errorMessage,
        next_retry_at: isExhausted ? null : DeadLetterQueue.calculateNextRetry(nextCount),
        status: isExhausted ? "dropped" : "retrying",
        updated_at: now,
      };
    }

    // Sucesso no retry
    return {
      ...record,
      retry_count: nextCount,
      status: "resolved",
      record_state: "active",
      resolved_at: now,
      next_retry_at: null,
      resolution_notes: "Successfully processed on retry attempt",
      updated_at: now,
    };
  }
}
