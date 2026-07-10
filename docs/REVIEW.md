# PIBRAS — Revisão de Consistência e Potencial de Melhoria

> Revisão multi-agente da pasta completa. Escopo: inconsistências e oportunidades de melhoria.
> Status: **somente diagnóstico** — nenhum artefato do padrão foi alterado.
> Data: 2026-06-21 · Método: 4 agentes paralelos (schema/tipos/DDL · docs/governança · conformidade · arquitetura), com validação real (`jsonschema` Draft 2020-12 + `xmllint`) no corpus.

---

## Sumário executivo

No nível de **contrato de dados** (schema/tipos/DDL/exemplos/migração) o padrão está coerente e quase completo: o exemplo e os fixtures `.valid.` validam, os fixtures `.invalid.` falham, e a maioria dos bloqueios do review anterior (`.omo/evidence/`) já foi sanada. Os dois eixos de problema são:

1. **Deriva de status/versão.** Os artefatos rotulados "v0.1.0" já implementam quase tudo o que o README/VERSIONING/MBRAS-STANDARD descrevem como "v0.2 futura". A narrativa de autoridade ficou atrás do código.
2. **Ausência da camada de execução.** As três semânticas que justificam o padrão — exposição default-deny/mascaramento, survivorship/dedupe, retenção/DSAR — existem como **dados e prosa**, nunca como **código que as imponha ou teste**. Duas implementações podem "passar" no corpus e vazar PII de formas diferentes.

Há ainda um vazamento concreto **dentro do próprio corpus golden** (preço publicado no feed de um imóvel marcado "sob consulta") que merece correção imediata por ser material de referência.

---

## Achados priorizados (top 12)

| # | Sev. | Achado | Evidência |
|---|------|--------|-----------|
| 1 | Crítico | Artefatos "v0.1.0" já contêm TODAS as entidades ditas "v0.2 futura" (`Party`, `Ownership`, `ExposurePolicy`, `DataSubjectRequest`, `Organization`, `Tenant`…). README/VERSIONING/MBRAS-STANDARD descrevem-nas como inexistentes/futuras. | `schema/mbras.schema.json:2` vs `README.md:28-35`, `docs/VERSIONING.md:16-18` |
| 2 | Crítico | `Document.confidentiality`: `required` no schema **sem** default, mas Zod/DDL têm `default 'sensitive'`. Contrato de obrigatoriedade divergente. | `schema:585,595` · `types/mbras.ts:426` · `db/schema.sql:590` |
| 3 | Crítico | `Property.property_status`: DDL `NOT NULL DEFAULT 'draft'` vs schema/Zod obrigatório sem default. Gravação inconsistente API↔DB. | `schema:375` · `types/mbras.ts:279` · `db/schema.sql:329` |
| 4 | Alto | **Vazamento no corpus**: `portal-feed.valid.xml` publica `<Price>1750000000</Price>` do mesmo imóvel (MB18495) que `listing.public-masked.json` marca `price_display: on_request`. Contradiz `portal-feed-notes.md:17-20`. | `tests/golden/portal-feed.valid.xml:7` |
| 5 | Alto | Feature central (autorização default-deny/`ExposurePolicy`) é **100% não-executável**: nenhum código avalia as `expected_decisions`/projeções. A verificação atual só faz `JSON.parse`. | `README.md:72` · `tests/README.md:27` · `exposure-policy.default-deny.json:38-60` |
| 6 | Alto | `User` existe em schema e types, mas **não há `CREATE TABLE user` no DDL** (confirmado por grep). Entidade do MVP em 2 de 3 artefatos. | `schema:272`, `types/mbras.ts:176` · ausente em `db/schema.sql` |
| 7 | Alto | `Owner.address`/`Party.address` aceitam campos (`complement`, `neighborhood_id`, `latitude`, `longitude`, `geo_precision`, `formatted`) que o DDL não persiste → perda de dados ao gravar. | `schema:470,493` vs `db/schema.sql:275-280,428-433` |
| 8 | Alto | `code`: `MBRAS-PROPERTY-STANDARD §6.3` marca **obrigatório (✓)**, mas schema/DDL/types tratam como **opcional/nullable**. | `docs/MBRAS-PROPERTY-STANDARD.md:261` vs `schema:375`, `db/schema.sql:325` |
| 9 | Alto | `external_ids[]` com dois shapes incompatíveis: `{source, external_id}` (doc fundador) vs `{namespace, key, value}` (schema/v0.2/exemplo). | `docs/PIBRAS-STANDARD-v0.1.md:329,468` vs `schema` ExternalId |
| 10 | Alto | Precedência de regras da `ExposurePolicy` subespecificada para um motor real: ordem de escopos, match de `fields` por prefixo, resolução de empate, `default_decision: deny` × `exposure_level: public`. | `docs/exposure-policy.md:11-18` · `schema:638-656` (sem prioridade) |
| 11 | Alto | Mascaramento de PII depende de cada consumidor "fazer certo": sem camada de projeção de referência; papéis (`director`…) usados como string sem enum de papéis. | `schema:386,466` · `exposure_rule.field_visibility` |
| 12 | Alto | `examples/property.sample.json` é rotulado "v0.1.0 compatível", mas usa o shape `external_ids` v0.2. | `README.md:45,62` vs `examples/property.sample.json:4-10` |

---

## A. Consistência schema ↔ tipos ↔ DDL ↔ exemplos

Validação real: exemplo principal + 5 fixtures com envelope = **6/6 PASS**; `property.invalid-money.json` **rejeitado** corretamente. Convenções do README (snake_case, uuid, ISO 8601 UTC, centavos `{amount,currency}`, m², WGS84) conformes onde checadas.

Divergências entre representações (além dos itens #2, #3, #6, #7 acima):

- **[Médio] `AuditEvent.id`**: `integer` (schema/Zod) vs `BIGINT` (`db/schema.sql:796`). Ids > 2^53 perdem precisão como `number` JS. Mesma ressalva no par `*_amount BIGINT` de Money.
- **[Médio] Defaults só em Zod/DDL, ausentes no schema** (padrão recorrente): `Unit.dedupe_review_state` (`'unreviewed'`), `Geography.geography_type` (`'neighborhood'`), `MediaAsset.media_role/media_rights/visibility`. O JSON Schema não preenche default, mas a omissão da anotação `"default"` cria divergência documental.
- **[Médio] `Property.building_id` × `Unit.building_id`**: coexistem; a view `property_full` faz `COALESCE` (`db/schema.sql:899`) mas nenhuma constraint garante coerência. Documentar precedência (Property vence).
- **[Médio] `format: "uri"` em campos `["string","null"]`** (`Provenance.source_url` e ~5 outros): hoje inofensivo (format é anotação), frágil se promovido a assertion.
- **[Alto] `ExposureRule.id`** opcional em schema/Zod vs PK `NOT NULL` no DDL — documentar como server-generated.
- **[Baixo] `AuditEvent.change_type`**: enum em schema/Zod vs `TEXT` livre no DDL (`:802`) sem `CHECK`.
- **[Baixo] Coords WGS84**: `DOUBLE PRECISION` sem `CHECK` de range no DDL (schema/Zod limitam −90/90, −180/180).
- **[Baixo] Tabelas DDL-only** (`lead_interest`, `visit`, `offer`, `comparable_property`, `price_history`, `status_history`, `ingestion_record`, `pending_change`): esperado (operacionais), mas a assimetria não está anotada no schema/README.

## B. Coerência de docs e governança

**Links: nenhum quebrado.** Todos os hyperlinks do README e refs a artefatos resolvem; a one-liner de verificação do README executa (`PASS`). Ressalva: `docs/manifesto.md`, `docs/mvp.md`, `schemas/*`, `examples/*.example.json` aparecem só como **layout proposto** no bloco ```txt``` do draft §20 — não são links, mas o texto no presente pode induzir a lê-los como existentes.

- **[Crítico] MBRAS-PROPERTY-STANDARD é "fonte de verdade" mas não documenta** `Party`/`Ownership`/`ExposurePolicy`/`DataSubjectRequest`/`Geography`/`Organization`/`Tenant`/`AuditEvent` que o código implementa (só cita no changelog `:495`).
- **[Médio] `docs/lgpd.md`, `docs/exposure-policy.md`, `docs/entity-resolution.md`** são normativos mas ausentes do índice de autoridade do README.
- **[Médio] `GOVERNANCE.md`/`RFC_PROCESS.md`** não referenciados pelo README; `VERSIONING.md:22-34` cita "RFC aprovada" sem link para `RFC_PROCESS.md`.
- **[Médio] Três mecanismos de autorização** (`field_visibility`, `ExposureRule`, `ExposurePolicy`) coexistem no DDL sem o doc canônico fixar a precedência em runtime (o `exposure-policy.md:7` diz "ExposurePolicy primeiro, ExposureRule como fallback" — replicar no MBRAS-STANDARD §2.6).
- **[Médio] Moeda no doc fundador** usa `asking_price_brl` em reais — formato que o canônico trata como **inválido**; sem aviso de superação.
- **[Médio] Estado "Aceito"** (`VERSIONING.md:10`) sem documento nesse estado e sem transição correspondente no `RFC_PROCESS.md` (passo final é só "publicar release notes").
- **[Baixo]** Header do MBRAS-STANDARD diz "rascunho para revisão" vs README "fonte de verdade"; `confidentiality_level` (fundador) nunca adotado; `AGENTS.md` é placeholder de 1 linha; `LICENSE`/`AGENTS.md` em inglês vs resto em PT.

## C. Conformidade — fixtures golden e mappings

Todos os fixtures se comportam conforme o nome; sem falso-positivo/negativo. Todos os campos PIBRAS citados nos 4 mappings **existem** no schema/types; `conformance-cases.json` tem 10 casos sem ids/paths duplicados e sem fixtures órfãos.

- **[Alto]** Vazamento de preço no corpus (item #4).
- **[Médio] `property.invalid-money.json` sem `schema_ref`** — único fixture negativo sem o campo que todos os `.valid.` têm; um runner fiel ao README não saberia contra qual `$def` validar. Adicionar `"schema_ref": "#/$defs/Property"`.
- **[Médio]** O mesmo fixture invalida por **3 motivos** (`_brl` + `provenance` ausente + `audit` ausente), mas o `reason` cobre só o `_brl`; runner que pare no 1º erro reprova "pelo motivo errado". Incluir `provenance`/`audit` válidos para isolar a causa.
- **[Baixo]** `conformance-cases.json` usa ids que divergem do `id` interno de 2 fixtures (`property.invalid-money.json`, `import-row.pending-change.json`) — quebra rastreabilidade.
- **[Baixo]** `unit.duplicate-candidate.json:14` usa `decision: "auto_merge"`, valor inexistente no enum `DedupeReviewState`. Mapear para estado do schema ou marcar como vocabulário de pipeline.
- **[Baixo]** `mappings/v0.1.0-code-to-v0.2.md:135` cita `applied_rule_ids` sem contraparte no schema/types (não há tipo de resultado de decisão). Definir `PolicyDecisionResult` ou marcar como contrato de runtime.

## D. Arquitetura e riscos de design

- **[Alto] Autorização não-executável** (item #5): o valor inteiro do padrão repousa sobre uma política que nenhum código avalia — reintroduz o risco de vazamento que o padrão diz prevenir.
- **[Alto] Precedência de regras subespecificada** (item #10).
- **[Alto] Mascaramento depende do consumidor** (item #11): `Property` carrega `min_accepted_price`/`owners[]` e `Owner`/`Party` carregam `tax_id`/`phone` no mesmo objeto canônico; qualquer serializador ingênuo (feed, CSV, log) vaza sem uma camada de projeção de referência.
- **[Médio] `mask` sem mecânica definida**: `listing.public-masked.json` mostra `address.number: null` e `price: "Sob consulta"` (string PT-BR no payload) — duas estratégias, nenhuma normativa.
- **[Médio] `Geography` órfã** (confirmado): `building.addr_neighborhood_id`/`unit.addr_neighborhood_id` referenciam `neighborhood(id)` (`db/schema.sql:153,210`), não `geography`. A entidade-alvo só é referenciada por si mesma (`parent_id`, `:125`). Migração incompleta na prática.
- **[Médio] LGPD declarativa, não acionável**: `retention_policy_id` é `TEXT` livre (sem entidade `RetentionPolicy`); DSAR `deletion` sem efeito concreto (`audit_log_ref TEXT` solto); `marketing_consent` existe em `Owner` mas não migrou para `Party`.
- **[Médio] PII sem classificação legível por máquina**: campos sensíveis identificados só por comentário em prosa; a lista de 13 campos vive em `draft §7.1` como texto — divergirá do schema. Falta vocabulário tipo `x-pii`/`x-sensitivity`.
- **[Médio] Entity resolution**: âncora `Unit` é sólida, mas o fluxo "externo entra como sugestão" só tem fixture para update de preço; faltam casos para banda 0,75–0,95, tentativa externa de alterar `owner`/`tax_id`, e merge revertido.
- **[Baixo] `Owner` × `Party`** coexistem sem critério/data de descontinuação; `Document.owner_id` (`:585`) ainda aponta para `owner`, não `party` — risco de divergência de PII na janela.
- **[Baixo] Versionamento auto-inconsistente**: `version: "0.1.0"` e `$id ...mbras.com.br` vs fixtures `version: "0.2-draft"` e posicionamento neutro do projeto.

---

## Prometido-mas-ausente

Declarado em docs, sem o artefato que o torna real:

- **Runner de conformidade / validador semântico** (`README.md:72`, `tests/README.md:27`, `VERSIONING.md:34`) — gap dominante.
- **Avaliador de `ExposurePolicy`** que consuma `expected_decisions`/`projection_expectation`.
- **OpenAPI inicial** (entregável do MVP, `draft:1247,1338`; princípio "API-first").
- **Survivorship executável** — regras campo a campo (`draft:871-887`) sem tabela nem fixtures além de um caso de preço.
- **Auditoria de leitura sensível** — `audit_sensitive_reads: true` sem mecanismo nem fixture.
- **`User`** sem fixture golden — e ausente do DDL (item #6).
- **Selo/checklist de compatibilidade** ("PIBRAS Compatible", "Secure Exposure Ready", `draft:153-162`).

---

## Melhorias priorizadas (impacto/esforço — maior impacto primeiro)

1. **Escrever o runner de conformidade** (Node + Ajv) validando cada `payload` contra `schema_ref` **e** avaliando `ExposurePolicy` sobre `expected_decisions`. Converte o padrão de "documento" em "verificável" e fecha o maior risco. (Alto/Médio)
2. **Especificar formalmente o algoritmo de avaliação de política**: ordem de escopos, match de `fields` por prefixo, resolução de empate, mecânica de `mask` por tipo (preço→faixa, CEP→prefixo, `tax_id`→null). Pré-requisito do runner. (Alto/Baixo-Médio)
3. **Camada de projeção de referência (mask/redact)** com fixtures de entrada/saída para público, broker, diretoria. Elimina vazamento por serializador ingênuo. (Alto/Médio)
4. **Marcar PII no schema** (`x-pii`, `x-sensitivity`) e gerar a lista de campos sensíveis a partir do schema. (Alto/Baixo)
5. **Conectar `Geography`**: migrar FKs `addr_neighborhood_id → geography` ou documentar `neighborhood` como tabela física e `Geography` como view canônica. (Médio/Baixo)
6. **`RetentionPolicy` como entidade** (prazo, ação delete/anonymize, base legal) e ligar DSAR `deletion` a um efeito concreto. (Médio/Médio)
7. **Adicionar `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`** — credibilidade/adoção de um padrão aberto. (Médio/Baixo)
8. **CI mínimo (GitHub Actions)** rodando o runner + checks de SemVer/compatibilidade; satisfaz "comando de verificação executado" do `VERSIONING.md:34`. (Médio/Baixo)
9. **Expandir o corpus golden**: banda de review de dedupe, sobrescrita externa de PII, DSAR-deletion, `needs_approval` ponta a ponta, fixture de `User`. (Médio/Baixo)
10. **Alinhar `version`/`$id`** com o estágio (0.2-draft) e mover `$id` para domínio neutro antes de publicação externa. (Baixo/Trivial)

**Quick wins de credibilidade** (baixo esforço): atualizar o índice do README com docs e governança faltantes (B); corrigir o preço no `portal-feed.valid.xml` (#4); adicionar `schema_ref` ao fixture negativo (C); criar `CREATE TABLE user` no DDL (#6); preencher/remover `AGENTS.md`.

---

## Status do review prévio (`.omo/evidence/pibras-v0.2-reconciliation-code-review.md`)

O review anterior deu **BLOCK / REQUEST_CHANGES**. A maior parte já foi endereçada:

- **RESOLVIDO** — `code` não é mais `required` no schema; `property.valid.json` omite `code` de propósito, provando o payload v0.2 canônico.
- **RESOLVIDO** — fixtures "valid" agora são envelopes (`tests/README.md:3`: validar o `payload`); `additionalProperties:false` deixa de quebrá-los. *Ressalva: o runner que aplica esse contrato ainda não existe.*
- **RESOLVIDO** — `Document`/`PublicationChannel`/`User`/`AuditEvent` agora existem em schema+types (com a ressalva de que **`User` falta no DDL**).
- **PARCIAL** — verificação local ainda só faz `JSON.parse` e testa só o prefixo do XML, não valida bem-formação.

**Ainda aberto:** o runner/avaliador semântico (gap dominante) e a tabela `user` no DDL.

---

## Verificado e correto (não é problema)

Registrado para evitar retrabalho: exemplo e fixtures `.valid.` validam contra o schema; `property.invalid-money.json` é rejeitado; `money.centavos.expected.json` (R$ 17.500.000,00) correto; `exposure-policy.default-deny.json` coerente com a semântica; `portal-feed.valid.xml` é bem-formado (`xmllint`); todos os links do README resolvem; campos dos 4 mappings existem no schema/types; `conformance-cases.json` sem duplicatas/órfãos; convenções de nomenclatura/tipo/tempo consistentes nas três representações.
