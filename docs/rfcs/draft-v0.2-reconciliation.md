# RFC Draft: reconciliação e aceitação do padrão v0.2

## Metadados

| Campo | Valor |
|---|---|
| RFC ID | Unassigned |
| Status | Draft; não normativo |
| Versão-alvo | v0.2 |
| Implementação | Concluída em `main`; pendente de aceitação formal |
| Compatibilidade esperada | Incompatível para writers de DDL; compatível para leitores |
| Data | 2026-08-21 |
| Revisores | Nenhum registrado |

> Este arquivo é `Draft` e `RFC ID: Unassigned`. Conforme `RFC_PROCESS.md`,
> criá-lo não equivale a submeter, aceitar ou implementar a proposta. A
> transição para `Accepted` exige aprovação registrada de pelo menos dois
> mantenedores nomeados e a atualização de `governance/release-policy.yaml`
> para `phase: rfc_accepted`.

## Resumo

Propõe aceitar como padrão v0.2 o conjunto de contratos já reconciliado em
`main`: JSON Schema, Zod/TypeScript, DDL PostgreSQL, OpenAPI, fixtures golden
e documentos normativos, todos verificados por gates automatizados.

A implementação está pronta e verificável; o que falta é o rito de governança.
Esta RFC existe para que a v0.2 seja aceita por decisão registrada de
mantenedores, e não por acúmulo de commits.

## Problema

A v0.2 vem sendo descrita como *draft* desde a sua concepção
(`docs/PIBRAS-STANDARD-v0.2-draft.md`), enquanto os artefatos técnicos já
convergiram para ela. Isso cria três problemas concretos:

1. **Nenhum implementador sabe a que se conformar.** O README aponta a v0.2
   como "próximo padrão proposto", mas `schema/`, `types/` e `db/` já
   implementam a v0.2 reconciliada. Prosa e código discordam.
2. **O processo de governança nunca foi exercido.** `RFC_PROCESS.md` descreve
   estados e fluxo; nenhuma RFC chegou a `Accepted`. Para um padrão que se
   apresenta como governado, isso é um problema de credibilidade, não apenas
   de burocracia.
3. **A cadeia de release está travada.** `governance/release-policy.yaml`
   permanece em `phase: identity`. Sem RFC aceita não há `rfc_accepted`, sem
   `rfc_accepted` não há `legal_approved`, e portanto não há v1.0.0.

## Proposta

Aceitar a v0.2 como padrão vigente, com o escopo exato já implementado e
verificado. Nenhuma mudança de contrato adicional é proposta aqui: esta RFC
ratifica o que existe, e não introduz superfície nova.

Ao ser aceita:

1. `docs/PIBRAS-STANDARD-v0.2-draft.md` passa a `docs/PIBRAS-STANDARD-v0.2.md`
   com `Status: normativo`;
2. `README.md` passa a apontar a v0.2 como fonte de verdade, movendo a v0.1.0
   para histórico;
3. `governance/release-policy.yaml` avança para `phase: rfc_accepted`,
   registrando os mantenedores aprovadores e as referências imutáveis de
   revisão;
4. `docs/VERSIONING.md` registra a promoção conforme a sua própria regra.

## Entidades e campos afetados

Todas as mudanças já estão em `main`. Detalhe completo com antes/depois em
[`docs/migrations/v0.1.0-to-v0.2.md`](../migrations/v0.1.0-to-v0.2.md).

### Breaking (writers de banco)

| Mudança | Superfície |
|---|---|
| `audit_log.change_type`: `TEXT` → enum `audit_change_type NOT NULL` | DDL |
| `trust_tier`: adicionado `CHECK (trust_tier BETWEEN 1 AND 6)` | DDL |
| `ownership`: `OR` inclusivo → `num_nonnulls(unit_id, property_id) = 1` | DDL |
| `ownership`: participação agregada limitada a 100% por trigger | DDL |
| `media_asset`: `scope='listing'` passa a exigir `listing_id` | DDL |

Leitores não são afetados: nenhum campo foi removido nem renomeado.

### Aditivas e de conformidade

| Mudança | Superfície |
|---|---|
| `ExposureRule.field_visibility`: `default: {}` explícito | JSON Schema |
| `z.record(z.unknown())` → `z.record(z.string(), z.unknown())` | Zod v4 |
| 10 campos required deixam de ter `.default()` silencioso em Zod | Zod |
| 34 objetos passam a `.strict()`, espelhando `additionalProperties: false` | Zod |
| `property_public`: projeção pública governada, fail-closed | DDL |
| Projeção schema.org executável a partir de `property_public` | mappings |

## Compatibilidade

**Janela.** A v0.1.0 permanece legível durante toda a v0.2. Os aliases
`schema/mbras.schema.json` e `types/mbras.ts` são caminhos de compatibilidade
declarados e **não podem** ser removidos antes da v2.0.

**Para leitores.** Compatível. Nenhuma remoção ou renomeação de campo.

**Para writers de banco.** Incompatível nos cinco pontos acima. Um writer que
gravava `change_type` livre, `trust_tier` fora de 1–6, titularidade em dois
eixos simultâneos, participação somando mais de 100% ou mídia de listing sem
`listing_id` passa a ser rejeitado pelo banco. Em todos os casos o dado
anterior era ambíguo ou inválido segundo o próprio padrão; a mudança torna a
regra executável em vez de documental.

**Migração.** Ver §Plano de migração.

## Segurança e LGPD

Esta RFC não afeta bases legais, DSAR, retenção ou compartilhamento. Ela
ratifica controles que endurecem a exposição:

- **`property_public` é fail-closed.** Cinco condições independentes precisam
  ser verdadeiras para um imóvel aparecer: listing `exposure_level` público,
  publicado, ativo, não expirado e em canal ativo. Qualquer revogação retira a
  linha imediatamente, porque a view consulta as tabelas base.
- **Coordenadas públicas nunca excedem duas casas decimais** (~1 km),
  independentemente da configuração do listing.
- **`address_display = 'hidden'`** anula cidade, estado, bairro, coordenadas e
  nome do edifício.
- **Matrícula, PII, documentos e scores internos** não são selecionáveis na
  superfície pública — a impossibilidade é estrutural, não procedural.
- **Caso default-deny exigido pelo processo:** um imóvel sem listing
  qualificado não aparece em `property_public`. Verificado em
  `tests/postgres/property_public.sql`.

## Exemplos

Antes (v0.1.0), DDL aceitava qualquer texto e titularidade ambígua:

```sql
change_type   TEXT,                      -- insert | update | delete
CHECK (unit_id IS NOT NULL OR property_id IS NOT NULL)
```

Depois (v0.2), a regra é executável:

```sql
change_type   audit_change_type NOT NULL,
CHECK (num_nonnulls(unit_id, property_id) = 1)
```

Antes, o SDK TypeScript aceitava um payload que o schema canônico rejeitava:

```ts
ExposurePolicy.parse({ id, resource_type, exposure_level, created_at, updated_at })
// aceito: default_decision recebia "deny" silenciosamente
```

Depois, ambos exigem decisão explícita:

```ts
ExposurePolicy.parse({ ... })  // lança: default_decision é obrigatório
```

## Testes de conformidade

Toda mudança tem gate executável; nenhuma depende de revisão manual.

| Gate | Comando | Cobre |
|---|---|---|
| Paridade de contratos | `uv run scripts/check_contract_parity.py` | JSON Schema ↔ Zod ↔ DDL, incluindo `PIBRAS-PAR-005` (defaults em campos required) e `PIBRAS-PAR-006` (strictness) |
| Invariantes de domínio | `uv run scripts/check_domain_invariants.py` | coerência Building/Unit/Property |
| Conformidade | `uv run scripts/validate_conformance.py` | fixtures golden positivas e negativas |
| OpenAPI | `uv run scripts/validate_openapi.py` | superfície de referência e segurança |
| Tipos | `npm run typecheck && npm run test:types` | 63 testes |
| Banco real | `psql -f db/schema.sql` + `tests/postgres/property_public.sql` | DDL em PostgreSQL 16 e comportamento fail-closed |

Todos rodam em CI a cada PR, aplicando o DDL a um PostgreSQL 16 limpo.

## Plano de migração

Para operadores com dados v0.1.0 em produção:

1. **Auditar antes de migrar.** Identificar linhas que violarão as novas
   restrições:

   ```sql
   SELECT id FROM audit_log WHERE change_type NOT IN ('insert','update','delete');
   SELECT id FROM ownership WHERE num_nonnulls(unit_id, property_id) <> 1;
   SELECT unit_id, SUM(ownership_pct) FROM ownership
     WHERE record_state='active' AND owner_role='owner'
     GROUP BY unit_id HAVING SUM(ownership_pct) > 100;
   SELECT id FROM media_asset WHERE scope='listing' AND listing_id IS NULL;
   ```

2. **Corrigir os dados**, não relaxar as restrições. Cada violação indica
   ambiguidade real: titularidade em dois eixos, participação impossível ou
   mídia de anúncio sem anúncio.

3. **Aplicar o DDL** em transação, com rollback disponível.

4. **Rodar os gates** contra o banco migrado antes de expor qualquer canal.

**Rollback.** As restrições podem ser removidas com `ALTER TABLE ... DROP
CONSTRAINT`; o enum `audit_change_type` exige converter a coluna de volta para
`TEXT`. Nenhum dado é destruído pela migração.

**Exclusões.** Entidades comerciais e de inteligência experimentais
(`property_intelligence`, `lead_interest`, `visit`, `offer`) permanecem fora da
conformidade v1 e não são objeto desta RFC.

## Alternativas consideradas

**Manter a v0.2 como draft indefinidamente.** Rejeitada: prosa e código já
discordam, e nenhum implementador externo consegue determinar o alvo.

**Aceitar apenas as mudanças aditivas, adiando as breaking.** Rejeitada: as
cinco mudanças breaking são precisamente as que tornam executáveis regras que
o padrão já declarava. Adiá-las preservaria a divergência entre documento e
enforcement.

**Publicar como v1.0.0 diretamente.** Rejeitada: a v1.0.0 exige licença
aprovada, identidade neutra confirmada, release assinado e — criticamente —
evidência de interoperabilidade externa. Nada disso depende desta RFC, e
antecipar o número da versão não anteciparia a maturidade.

## Questões abertas

1. **Quem são os mantenedores aprovadores?** `RFC_PROCESS.md` exige pelo menos
   dois nomes com datas e referências imutáveis de revisão. Entrada externa
   obrigatória; não pode ser inferida.
2. **A promoção do arquivo draft deve ocorrer nesta RFC ou em commit
   separado?** Recomenda-se separado, para que a aceitação seja um commit de
   governança auditável e a renomeação não se misture ao registro da decisão.
3. **Licenciamento permanece bloqueante para publicação**, ainda que não para
   a aceitação da RFC. `LICENSE` continua com "License decision pending".
4. **RESO permanece fora de escopo** por questão jurídica registrada em
   `mappings/reso-to-pibras.md`, não por limitação técnica.
