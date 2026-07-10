# PIBRAS — Re-revisão (verificação das correções)

> Status: historical and non-authoritative


> Follow-up de [`docs/REVIEW.md`](REVIEW.md), após as correções executáveis (runner, fixtures, contrato, docs).
> Status: **somente verificação** — nenhum arquivo do padrão foi alterado nesta revisão.
> Data: 2026-06-21 · Método: 3 agentes paralelos + verificação independente por execução real.

## Veredito

As correções são **reais e verificadas**, não cosméticas. O runner é um gate genuíno (provado por mutation tests: falha quando deve), as 4 correções de contrato estão completas e consistentes nas 3 camadas, a **deriva de status/versão (achado crítico anterior) foi resolvida**, e **nenhuma regressão** foi introduzida. Restam buracos de cobertura no runner, pendências de contrato fora do escopo das 4 correções, e o **próprio draft v0.2 ficou defasado** frente ao que já foi implementado.

## Verificação independente executada

| Verificação | Ferramenta real | Resultado |
|---|---|---|
| Runner de conformidade | `python3` + `jsonschema` (reproduzi a execução) | **PASS** (EXIT 0) |
| Runner é gate real | 18 mutation tests em cópias `/tmp` | 13/18 detectadas (5 buracos — ver abaixo) |
| Tipos `types/mbras.ts` | `tsc --noEmit` (TS 6.0.3, zod 4.4.3, strict) | **PASS** (EXIT 0) — *gap "tsc" que você não conseguiu, fechado* |
| DDL `db/schema.sql` | parser real do Postgres (libpg_query v7.14) | **148 statements OK**; `CREATE TABLE "user"` presente; 36 tabelas, 47 FKs, 0 órfãs |
| Exemplo + 6 envelopes golden | `jsonschema` Draft 2020-12 | **6/6** conformes ao `expected_result` |

*Postgres vivo não foi possível (sem root/sudo, sem wheel aarch64). A validação de sintaxe/estrutura via libpg_query é parcial: cobre sintaxe e existência de FK-alvo, não ordem de execução nem checagem semântica completa.*

## Correções confirmadas (RESOLVIDO)

| Achado anterior | Evidência |
|---|---|
| #2 `Document.confidentiality` obrigatoriedade/default divergente | Saiu de `required`; default `sensitive` nas 3 (`schema:595` · `types:426` · `db:620`) |
| #3 `Property.property_status` default inconsistente | `draft` nas 3 (`schema:383` · `types:279` · `db:352`) |
| #6 `User` ausente no DDL | `CREATE TABLE "user"` (`db/schema.sql:102`); FKs p/ `tenant`/`organization` resolvem |
| #7 Endereço de `Owner`/`Party` truncado no DDL | Address completo nas **duas** tabelas, incl. `addr_formatted` (`db:291-303`, `:451-463`) |
| #4 Vazamento de preço no corpus | `portal-feed.valid.xml` sem `<Price>`; `<PriceDisplay>on_request` (`:7`) — e o runner falha se reintroduzido |
| C: fixture inválido sem `schema_ref` | `property.invalid-money.json:3` agora declara `schema_ref` e falha **só** pelo `_brl` |
| Gap dominante: runner/avaliador ausente | `scripts/validate_conformance.py` valida schema + **avalia `ExposurePolicy`** (`:163-203`) + feed |
| Deriva de status v0.1.0↔v0.2 (Crítico) | README inverte a narrativa (`README.md:33-40`: "a baseline já contém os alvos v0.2") |
| Docs normativos fora do índice | `README.md:19-21` lista lgpd/exposure-policy/entity-resolution; `:17-18` lista GOVERNANCE/RFC_PROCESS |
| `code` obrigatório no MBRAS-STANDARD | `MBRAS-PROPERTY-STANDARD.md:261` agora opcional, aponta `external_ids[]` |

Colaterais positivos: `CHECK` de WGS84 e Address completo entraram nas tabelas de PII (`owner`/`party`); `property_status`/`confidentiality` ganharam anotação `"default"` no JSON Schema.

## Buracos de cobertura do runner (novos achados)

Mutation tests que **passaram quando deveriam falhar**:

- **[Alto] Sem `FormatChecker`** — UUID/`date-time`/`email`/`uri` inválidos num fixture `.valid.` nunca falham (mutação "UUID quebrado" passou). Correção de 1 linha: `Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)`.
- **[Alto] `projection_expectation` é decorativa** — o mascaramento/projeção que o caso "public-masked" promete não é executado; vazar rua/preço no payload com `price_display:visible` ainda passa. Implementar o projetor e comparar com `projection_expectation`.
- **[Média] XML não-defensivo** — XML malformado derruba o runner com traceback `ParseError` (em vez de `FAIL` limpo); e a regra de preço só barra `<Price>` se presente, não exige ausência sob `on_request`.
- **[Média] Fixture `invalid` sem `schema_ref` não é validado** — retorno antecipado pula a checagem; exigir `schema_ref` sempre que `expected_result == "invalid"`.
- **[Baixa] Ramo `default_decision` sem cobertura** — adicionar uma `expected_decision` sobre campo/role sem regra explícita.

## Pendências de contrato (fora do escopo das 4 correções)

Permanecem do relatório anterior — nenhuma é regressão:

| Item | Status |
|---|---|
| `AuditEvent.id` `integer` (schema/Zod) vs `BIGINT` (DDL) — perda de precisão > 2^53 | ABERTO |
| `ExposureRule.id` opcional em schema/Zod vs PK NOT NULL no DDL | ABERTO |
| `format:"uri"` em campos `["string","null"]` (`source_url` etc.) | ABERTO |
| Defaults só em DDL/Zod ausentes no schema (`dedupe_review_state`, `geography_type`, `media_*`) | PARCIAL (melhorou nos 2 corrigidos) |
| `Property.building_id` × `Unit.building_id` sem constraint de coerência | ABERTO |
| `Geography` órfã: building/unit→`neighborhood`, owner/party→`geography`; endereços de imóvel não usam `geography` | PARCIAL |
| `AuditEvent.change_type` `TEXT` sem `CHECK`/enum no DDL | ABERTO |
| WGS84 sem `CHECK` em `building`/`unit` (resolvido só em owner/party) | PARCIAL |
| `Document.owner_id` → `owner` (não `party`) | ABERTO |
| `Owner` × `Party` coexistem sem critério de descontinuação; `marketing_consent` não migrou p/ Party | ABERTO |

## Revisão do draft v0.2 (`docs/PIBRAS-STANDARD-v0.2-draft.md`)

O foco pedido. O draft **ficou defasado** em relação aos artefatos que já foram implementados:

- **[Alto] Banner e §5.0 no tempo errado** (`:10`, `:280-284`): tratam a publicação do mapping de reconciliação como tarefa futura — o arquivo `mappings/v0.1.0-code-to-v0.2.md` **já existe** — e redigem a "decisão v0.2" no futuro, embora schema/DDL/types já implementem `Party`/`Ownership`/`ExposurePolicy`/`Geography`/`DataSubjectRequest`. Reescrever no passado.
- **[Alto] §20 "Próxima ação recomendada"** (`:1456-1498`): lista como entrega futura artefatos que **já existem** (README, GOVERNANCE, RFC_PROCESS, mappings, docs normativos, `tests/golden/*`) e, ao mesmo tempo, cita caminhos que **nunca foram criados** (`schemas/`, `examples/*.example.json`, `docs/manifesto.md`, `docs/mvp.md`) e nomes de fixture divergentes do real (`portal-feed.valid.expected.xml` vs o real `portal-feed.valid.xml`). Reconciliar com a árvore real.
- **[Média] Promessas normativas sem artefato**: `PolicyDecisionResult`/`applied_rule_ids` ainda não existem como tipo; `audit_sensitive_reads` permanece como flag sem mecanismo/fixture. OpenAPI inicial, `RetentionPolicy`, PII legível por máquina, survivorship e DSAR `deletion` foram endereçados nas atualizações abaixo.
- **[Média] Survivorship por campo** (§8.4, `:871-887`) só em prosa; faltam fixtures para sobrescrita externa de `owner`/`tax_id` e para a banda de revisão 0,75–0,95.
- **[Média] Precedência de política ainda incompleta para um motor**: `ExposurePolicyRule` não tem campo `priority`/ordem (`schema:623-636`); o runner devolve o 1º `allow` encontrado, sem resolver empate "mais restritiva vence" (regra 5 do draft, `:667`).
- **[Baixo] `applied_rule_ids`** prometido (`:671,695`) sem tipo `PolicyDecisionResult`; `version` do schema ainda `0.1.0` e `$id` em `mbras.com.br`, apesar do posicionamento neutro.

Pendências de docs ainda abertas/parciais: shape `external_ids` `{source,external_id}` no doc fundador sem marca de superado (ABERTO); `_brl` do fundador sem aviso in-loco (PARCIAL); estado "Aceito" do VERSIONING sem transição correspondente no RFC_PROCESS (PARCIAL); "RFC aprovada" sem hyperlink (PARCIAL).

## Prontidão para promoção a v0.2 estável

Gates 2–9 do `VERSIONING.md` essencialmente **OK** (README, de/para, schema, Zod, DDL, exemplos, golden, comando de verificação). **Bloqueadores:**

1. **Rito formal ausente** — não há RFC aprovada nem documento no estado "Aceito"; o `RFC_PROCESS.md` sequer define como se atinge "Aceito" (termina em "publicar release notes").
2. **O draft precisa ser atualizado antes de virar estável** — §5.0 e §20 descrevem como futuro o que já existe e apontam paths/fixtures inexistentes; promover como está cristalizaria instruções erradas.
3. **Promessas normativas ainda sem artefato completo**: `PolicyDecisionResult`/`applied_rule_ids`, ampliar a API além da superfície mínima e mecanismo executável para `audit_sensitive_reads`.

## Recomendações priorizadas

Quick wins (baixo esforço, alto retorno de robustez):

1. Ligar `FormatChecker` no runner (1 linha) — fecha o buraco de UUID/data/email/uri.
2. Exigir `schema_ref` quando `expected_result == "invalid"`; `try/except` no parse do XML.
3. Sincronizar §5.0 e §20 do draft com a árvore real (passado + paths/fixtures corretos).
4. Sinalizar in-loco no doc fundador (`PIBRAS-STANDARD-v0.1.md`) que `{source,external_id}`, `_brl` e `confidentiality_level` foram superados.

Médio esforço (fecham as promessas centrais do padrão):

5. Implementar o projetor de `projection_expectation` (masking real) + casos de survivorship/dedupe faltantes.
6. Adicionar `priority` a `ExposurePolicyRule` e definir resolução de empate; expor `PolicyDecisionResult` com `applied_rule_ids`.
7. `RetentionPolicy` como entidade (prazo, ação, base legal) ligada a DSAR `deletion`; marcar PII com `x-pii`/`x-sensitivity` e gerar a lista a partir do schema.
8. Formalizar a RFC e a transição para "Aceito" no `RFC_PROCESS.md`; ampliar o OpenAPI mínimo conforme a API de referência evoluir.

## Atualização — 2026-06-21 (itens de médio esforço implementados)

Aplicados e verificados por execução real (runner **PASS**, `tsc` EXIT 0, DDL parseado por libpg_query sem FK órfã, 8/8 envelopes válidos; mutation tests confirmam que os novos checks falham quando devem):

- **Projetor de `projection_expectation`** — o runner agora aplica mascaramento e barra vazamento de preço/endereço (mutação de vazamento → FAIL), encerrando o buraco "projeção decorativa".
- **`priority` + empate na `ExposurePolicy`** — campo `priority` em schema/tipos; o avaliador resolve por maior precedência e, no topo empatado, deny vence allow; o fixture exercita o caso (mutação que zera `priority` → FAIL) e o ramo `default_decision`.
- **`RetentionPolicy`** — entidade em schema/tipos/DDL (enum `retention_action`), `retention_policy_id` como uuid em `Tenant`/`Party`, e DSAR com efeito concreto (`resolution_action` + `affected_record_ids`); fixtures `retention-policy.valid.json` e `data-subject-request.deletion-fulfilled.json`.
- **Classificação de PII** — campos sensíveis marcados com `x-pii`/`x-sensitivity` no schema; §7.1 do draft e `lgpd.md` apontam que a lista deriva do schema.
- **Survivorship** — tabela por campo + thresholds de dedupe no draft §8.4, com fixtures `pending-change.owner-pii-protected.json` e `unit.dedupe-review-band.json`.

Atualização adicional — OpenAPI inicial implementado em `openapi.yaml`, com validador próprio `scripts/validate_openapi.py` e comando documentado no README.

Permanecem como roadmap (não implementados): `PolicyDecisionResult`/`applied_rule_ids` como tipo do schema; RFC formal + estado "Aceito"; expansão de `x-pii` a todos os campos listados em §7.1; e ampliar a API de referência além da superfície mínima.
