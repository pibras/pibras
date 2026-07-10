// PIBRAS aligned contract fixture (synthetic green).
import { z } from "zod";

export const AuditChangeTypeSchema = z.enum([
  "create",
  "update",
  "delete",
  "merge",
  "split",
]);

export const AuditEvent = z.object({
  id: z.string().uuid(),
  entity_id: z.string().uuid(),
  change_type: AuditChangeTypeSchema,
  trust_tier: z.number().int().min(1).max(6).nullish(),
  occurred_at: z.string().datetime(),
});

export const ExposureRule = z.object({
  id: z.string().uuid(),
  exposure_level: z.enum(["public", "restricted", "private"]),
  field_visibility: z.record(z.string(), z.unknown()).default({}),
});
