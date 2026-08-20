import { randomUUID } from "node:crypto";
import type { SourceSystem } from "../../types/mbras.ts";

export type PollingStatus = "idle" | "running" | "paused" | "circuit_broken";

export interface PollingJobConfig {
  id?: string;
  source_id: string;
  source_system: SourceSystem;
  poll_interval_seconds?: number;
  max_consecutive_failures?: number;
  base_backoff_seconds?: number;
  last_sync_timestamp?: string | null;
}

export interface PollingJobState {
  id: string;
  source_id: string;
  source_system: SourceSystem;
  status: PollingStatus;
  poll_interval_seconds: number;
  max_consecutive_failures: number;
  base_backoff_seconds: number;
  last_sync_timestamp: string | null;
  current_lock_token: string | null;
  last_run_started_at: string | null;
  last_run_finished_at: string | null;
  consecutive_failures: number;
  next_poll_at: string;
}

export interface DeltaWindow {
  start_time: string;
  end_time: string;
  lock_token: string;
}

export class PollingScheduler {
  /**
   * Inicializa um novo estado de job de polling delta.
   */
  public static createJob(config: PollingJobConfig): PollingJobState {
    const now = new Date().toISOString();
    const interval = config.poll_interval_seconds ?? 300; // 5 minutos por padrão
    const nextPoll = new Date(Date.now() + interval * 1000).toISOString();

    return {
      id: config.id ?? randomUUID(),
      source_id: config.source_id,
      source_system: config.source_system,
      status: "idle",
      poll_interval_seconds: interval,
      max_consecutive_failures: config.max_consecutive_failures ?? 5,
      base_backoff_seconds: config.base_backoff_seconds ?? 30,
      last_sync_timestamp: config.last_sync_timestamp ?? null,
      current_lock_token: null,
      last_run_started_at: null,
      last_run_finished_at: null,
      consecutive_failures: 0,
      next_poll_at: nextPoll,
    };
  }

  /**
   * Tenta adquirir o lock para iniciar uma execução de polling delta.
   * Retorna a janela de tempo [start_time, end_time] ou null se o job já estiver rodando ou em circuit_broken.
   */
  public static acquireDeltaWindow(job: PollingJobState): { job: PollingJobState; window: DeltaWindow | null } {
    if (job.status === "running" || job.status === "circuit_broken" || job.status === "paused") {
      return { job, window: null };
    }

    const now = new Date();
    const lockToken = randomUUID();

    // Se nunca rodou antes, pega delta das últimas 24 horas por padrão
    const startTime =
      job.last_sync_timestamp ?? new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString();
    const endTime = now.toISOString();

    const updatedJob: PollingJobState = {
      ...job,
      status: "running",
      current_lock_token: lockToken,
      last_run_started_at: endTime,
    };

    return {
      job: updatedJob,
      window: {
        start_time: startTime,
        end_time: endTime,
        lock_token: lockToken,
      },
    };
  }

  /**
   * Finaliza uma execução bem sucedida de polling delta.
   */
  public static recordSuccess(job: PollingJobState, window: DeltaWindow, recordsFetched: number): PollingJobState {
    const now = new Date().toISOString();
    const nextPoll = new Date(Date.now() + job.poll_interval_seconds * 1000).toISOString();

    return {
      ...job,
      status: "idle",
      current_lock_token: null,
      last_sync_timestamp: window.end_time,
      last_run_finished_at: now,
      consecutive_failures: 0,
      next_poll_at: nextPoll,
    };
  }

  /**
   * Registra uma falha de polling, aplicando backoff exponencial e disparando circuit breaker se necessário.
   */
  public static recordFailure(job: PollingJobState, error: Error | string): PollingJobState {
    const now = new Date().toISOString();
    const failures = job.consecutive_failures + 1;
    const isCircuitBroken = failures >= job.max_consecutive_failures;

    // Backoff: base * 2^(failures - 1)
    const backoffSeconds = job.base_backoff_seconds * Math.pow(2, Math.min(failures - 1, 6));
    const nextPoll = new Date(Date.now() + backoffSeconds * 1000).toISOString();

    return {
      ...job,
      status: isCircuitBroken ? "circuit_broken" : "idle",
      current_lock_token: null,
      last_run_finished_at: now,
      consecutive_failures: failures,
      next_poll_at: nextPoll,
    };
  }
}
