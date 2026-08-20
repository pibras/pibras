import type {
  ExposurePolicy,
  PolicyAction,
  PolicyDecision,
  Property,
  Unit,
  MediaAsset,
  ChannelType,
} from "../../types/mbras.ts";

export interface PolicyEvaluationContext {
  action: PolicyAction;
  channel_type: ChannelType;
  caller_role: string; // e.g. "public_website", "external_portal", "internal_broker", "director"
}

export interface EvaluationResult {
  decision: PolicyDecision;
  reasons: string[];
  masked_fields: string[];
  denied_fields: string[];
  /** Campos permitidos por regras 'allow'. Vazio = sem restrição de allowlist. */
  allowed_fields: string[];
}

export interface ProjectedPropertyPayload {
  property: Partial<Property>;
  unit: Partial<Unit> | null;
  media_assets: MediaAsset[];
  evaluation: EvaluationResult;
}

export interface ApprovalRecord {
  approved_by: string | null;
  approved_at: string | null;
  approval_scope: string | null;
}

/**
 * Reduz uma entidade aos campos permitidos por regras 'allow'.
 *
 * Allowlist vazia significa "sem restrição declarada" e devolve a entidade
 * inteira, preservando o comportamento de políticas que só usam mascaramento.
 * Quando há allowlist, apenas os campos declarados sobrevivem — mais `id`,
 * que é o identificador do recurso e não um dado exposto.
 */
function allowlistFields<T extends Record<string, unknown>>(
  entity: T,
  allowedFields: string[],
): Partial<T> {
  if (allowedFields.length === 0) return { ...entity };
  const keep = new Set<string>([...allowedFields, "id"]);
  const projected: Partial<T> = {};
  for (const key of Object.keys(entity)) {
    if (keep.has(key)) {
      projected[key as keyof T] = entity[key as keyof T];
    }
  }
  return projected;
}

export class ExposurePolicyEvaluator {
  /**
   * Avalia uma ExposurePolicy para uma dada ação e canal, seguindo a semântica default-deny.
   */
  public static evaluate(
    policy: ExposurePolicy,
    context: PolicyEvaluationContext
  ): EvaluationResult {
    const reasons: string[] = [];
    const maskedFields: string[] = [];
    const deniedFields: string[] = [];

    // 1. Verificação de canais permitidos
    if (
      policy.allowed_channels.length > 0 &&
      !policy.allowed_channels.includes(context.channel_type) &&
      !policy.allowed_channels.includes("*")
    ) {
      return {
        decision: "deny",
        reasons: [
          `Channel '${context.channel_type}' is not in policy allowed_channels: [${policy.allowed_channels.join(", ")}]`,
        ],
        masked_fields: [],
        denied_fields: ["*"],
        allowed_fields: [],
      };
    }

    // 2. Verificação se a ação exige aprovação prévia
    if (policy.requires_approval_for.includes(context.action)) {
      return {
        decision: "needs_approval",
        reasons: [`Action '${context.action}' requires explicit administrative approval`],
        masked_fields: [],
        denied_fields: [],
        allowed_fields: [],
      };
    }

    // 3. Avaliação de regras ordenadas por prioridade decrescente
    const sortedRules = [...policy.rules].sort((a, b) => b.priority - a.priority);

    const allowedFields: string[] = [];
    let currentDecision: PolicyDecision = policy.default_decision ?? "deny";

    for (const rule of sortedRules) {
      const matchesAction = rule.actions.includes(context.action) || (rule.actions as string[]).includes("*");
      const matchesRole =
        rule.roles.length === 0 ||
        rule.roles.includes(context.caller_role) ||
        rule.roles.includes("*");

      if (matchesAction && matchesRole) {
        if (rule.effect === "allow") {
          currentDecision = "allow";
          reasons.push(`Rule '${rule.id ?? "anonymous"}' ALLOWED action '${context.action}'`);
          if (rule.fields.length > 0) {
            allowedFields.push(...rule.fields);
          }
        } else if (rule.effect === "deny") {
          currentDecision = "deny";
          reasons.push(`Rule '${rule.id ?? "anonymous"}' DENIED action '${context.action}'`);
          if (rule.fields.length > 0) {
            deniedFields.push(...rule.fields);
          } else {
            deniedFields.push("*");
          }
          break; // Deny explícito tem precedência
        }
      }
    }

    // 4. Regras automáticas de mascaramento para canais públicos
    if (context.channel_type === "website" || context.channel_type === "portal" || context.channel_type === "paid_ad") {
      if (policy.exposure_level === "confidential" || policy.exposure_level === "off_market") {
        maskedFields.push("address.street", "address.number", "address.complement", "asking_price");
        if (currentDecision === "allow") {
          currentDecision = "mask";
        }
      } else if (policy.exposure_level === "restricted") {
        maskedFields.push("address.number", "address.complement");
        if (currentDecision === "allow") {
          currentDecision = "mask";
        }
      }
    }

    return {
      decision: currentDecision,
      reasons,
      masked_fields: [...new Set(maskedFields)],
      denied_fields: [...new Set(deniedFields)],
      allowed_fields: [...new Set(allowedFields)],
    };
  }

  /**
   * Projeta os dados da Property e Unit aplicando os filtros de privacidade e mascaramento calculados.
   */
  public static projectForChannel(params: {
    property: Property;
    unit?: Unit | null | undefined;
    media_assets?: MediaAsset[] | undefined;
    policy: ExposurePolicy;
    context: PolicyEvaluationContext;
    approval_record?: ApprovalRecord | null | undefined;
  }): ProjectedPropertyPayload | null {
    const evalResult = this.evaluate(params.policy, params.context);

    // Approval gate: confidential/off_market properties require explicit
    // owner authorization before exposure to public channels.
    if (
      (params.policy.exposure_level === "confidential" || params.policy.exposure_level === "off_market") &&
      (params.context.channel_type === "portal" || params.context.channel_type === "website" || params.context.channel_type === "paid_ad")
    ) {
      const approval = params.approval_record;
      if (!approval || !approval.approved_by || !approval.approved_at) {
        return {
          property: {},
          unit: null,
          media_assets: [],
          evaluation: {
            decision: "deny",
            reasons: [
              "Ultra-luxury gate: confidential/off_market property requires explicit owner authorization for public channels. No valid approval_record provided.",
            ],
            masked_fields: [],
            denied_fields: ["*"],
            allowed_fields: [],
          },
        };
      }
    }

    // Somente 'allow' e 'mask' são publicáveis. 'deny' e 'needs_approval'
    // bloqueiam a projeção: emitir algo que aguarda aprovação equivale a
    // publicar sem ela.
    if (evalResult.decision !== "allow" && evalResult.decision !== "mask") {
      return null;
    }

    // Allowlist tem precedência: se alguma regra 'allow' declarou campos, só
    // eles (mais o identificador do recurso) sobrevivem à projeção. Sem isso a
    // projeção seria uma deny-list e vazaria qualquer campo não mascarado.
    const projectedProp: Partial<Property> = allowlistFields(
      params.property,
      evalResult.allowed_fields,
    );
    let projectedUnit: Partial<Unit> | null = params.unit
      ? allowlistFields(params.unit, evalResult.allowed_fields)
      : null;

    // Mascarar preço se solicitado
    if (evalResult.masked_fields.includes("asking_price")) {
      delete projectedProp.asking_price;
    }

    // Mascarar endereço na Unit
    if (projectedUnit?.address) {
      const addr = { ...projectedUnit.address };
      if (evalResult.masked_fields.includes("address.number")) {
        addr.number = null;
        addr.complement = null;
      }
      if (evalResult.masked_fields.includes("address.street")) {
        addr.street = null;
        addr.formatted = `${addr.neighborhood_raw ?? ""}, ${addr.city ?? ""}`.trim();
      }
      projectedUnit.address = addr;
    }

    // Filtrar mídias confidenciais se o canal for público
    const allowedMedia = (params.media_assets ?? []).filter((m) => {
      if (params.context.channel_type === "website" || params.context.channel_type === "portal") {
        return m.media_rights !== "restricted";
      }
      return true;
    });

    return {
      property: projectedProp,
      unit: projectedUnit,
      media_assets: allowedMedia,
      evaluation: evalResult,
    };
  }
}
