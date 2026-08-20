# RFC Draft: máquina de estados de ofertas e concorrência

## Metadados

| Campo | Valor |
|---|---|
| RFC ID | Unassigned |
| Status | Draft; não normativo |
| Versão-alvo | Não agendada |
| Implementação | Não iniciada |
| Compatibilidade esperada | Potencialmente incompatível para enums fechados e writers |
| Data | 2026-08-20 |
| Revisores | Nenhum registrado |

## Resumo

Propõe um contrato interoperável para versões de oferta, validade operacional, idempotência e prevenção de múltiplos aceites na mesma negociação. Estados de banco apoiam rastreabilidade e não comprovam efeito jurídico.

## Problema

A tabela `offer` atual existe apenas no DDL e possui `submitted`, `countered`, `accepted`, `rejected` e `withdrawn`. Não há contrato correspondente no JSON Schema/Zod, tabela de transições, prazo, idempotência, versão de termos ou escopo de concorrência.

## Proposta

### Estados candidatos

```text
draft -> submitted -> in_review -> countered
                     |             |
                     +-> accepted  +-> submitted (nova revisão)
                     +-> rejected
                     +-> withdrawn
                     +-> expired
                     +-> superseded
```

A tabela completa de eventos, atores autorizados e transições permanece decisão aberta. Nenhum estado acima é canônico antes da aprovação desta RFC.

### Campos candidatos

| Campo | Tipo | Observação |
|---|---|---|
| `buyer_party_id` | UUID nullable | Substituição progressiva de `buyer_ref`; PII. |
| `negotiation_id` | UUID | Escopo da concorrência e de um aceite ativo. |
| `idempotency_key` | UUID | `UNIQUE(property_id, idempotency_key)`. |
| `terms_payload` | JSONB | Snapshot imutável dos termos estruturados. |
| `terms_hash` | TEXT | `sha256:<hex>` sobre canonicalização versionada. |
| `previous_offer_id` | UUID nullable | Encadeia contrapropostas sem sobrescrever termos. |
| `revision_number` | INTEGER | Único por negociação/ramo definido. |
| `valid_until` | TIMESTAMPTZ nullable | Prazo operacional expresso; obrigatoriedade depende de decisão jurídica/domínio. |
| `received_at` | TIMESTAMPTZ | Tempo autoritativo do servidor. |

Replay com mesma chave e hash retorna o resultado existente. Mesma chave com hash diferente gera conflito de idempotência.

### Concorrência

O serviço canônico deve bloquear a negociação durante o aceite e o banco deve impor no máximo uma oferta `accepted` ativa por `negotiation_id`. O índice não deve usar apenas `property_id`, pois ciclos ou modalidades diferentes podem coexistir historicamente. Cascade para `superseded` precisa ocorrer na mesma transação e ser auditado.

### Canonicalização

A RFC final deve escolher um padrão identificável, incluindo ordenação de chaves, Unicode, números, `null`, versão e encoding. Um hash sem canonicalização e proteção de atualização não garante imutabilidade.

## Entidades e campos afetados

- novo `Offer` em `schema/mbras.schema.json` e `types/mbras.ts`;
- expansão de `offer`/`offer_status` em `db/schema.sql`;
- `PolicyResourceType += offer` nas três camadas;
- OpenAPI, exemplos e golden fixtures;
- possível recurso/entidade de negociação.

## Compatibilidade

A mudança não é presumida retrocompatível. Novos valores quebram consumidores com enums fechados; campos obrigatórios quebram writers; índices podem encontrar dados legados conflitantes.

Migração deve começar com campos nullable, auditar dados e gerar `idempotency_key` como UUID válido (`gen_random_uuid()` ou UUID determinístico especificado). Strings `legacy-<id>` não são válidas para coluna UUID.

## Segurança e LGPD

- `buyer_ref`, `buyer_party_id`, termos e documentos devem ser classificados por campo.
- `offer` precisa entrar no `PolicyResourceType` antes de alegar proteção via `ExposurePolicy`.
- logs devem evitar cópia integral de termos/PII.
- transições exigem autorização e trilha de ator, razão e timestamp.

## Exemplos

### Replay idempotente

```text
mesma property + mesma key + mesmo hash -> retorna oferta existente
mesma property + mesma key + hash diferente -> 409 IDEMPOTENCY_TERMS_MISMATCH
```

### Contraproposta

Uma contraproposta cria nova revisão com `previous_offer_id`; não altera o snapshot da revisão anterior.

## Testes de conformidade

- enums e campos alinhados nas três superfícies;
- replay idempotente e conflito de payload;
- hash reproduzível por duas implementações;
- transição não permitida rejeitada;
- corrida de dois aceites resulta em um único aceite;
- aceite vencido e expiração concorrentes são serializados;
- cascade é atômicos e auditável;
- consumidor sem permissão não lê PII da oferta.

## Plano de migração

1. auditar estados e múltiplos aceites existentes;
2. adicionar campos nullable e índices não únicos;
3. backfill de UUIDs válidos, snapshots e hashes após definir canonicalização;
4. publicar versão de compatibilidade e capability negotiation;
5. atualizar schema, Zod, DDL, OpenAPI e fixtures juntos;
6. habilitar constraints somente após validação;
7. promover por RFC aprovada.

## Alternativas consideradas

- manter `Offer` apenas operacional: reduz escopo, mas não cria interoperabilidade;
- event sourcing completo: adiado por complexidade;
- unicidade por `property_id`: rejeitada como excessivamente ampla.

## Questões abertas

- quais estados e atores são realmente interoperáveis;
- definição de negociação e encerramento/rescisão;
- quando `valid_until` é obrigatório;
- canonicalização dos termos;
- forma de assinatura e evidência externa.
