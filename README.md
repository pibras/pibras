# PIBRAS — Portfólio Imobiliário do Brasil

Camada e padrão aberto para organizar, importar, normalizar, governar e distribuir dados imobiliários no Brasil.

**PIBRAS é o padrão; a stack é apenas uma forma de implementar.**

## Percurso rápido para um consumidor

1. **Norma:** [`docs/PIBRAS-STANDARD-v0.2.md`](docs/PIBRAS-STANDARD-v0.2.md), aceita via [PIBRAS-RFC-001](docs/rfcs/accepted-001-v0.2-reconciliation.md) (2026-08-21), mais os documentos normativos listados abaixo.
2. **Aliases e caminhos históricos:** veja [Como resolver divergências](#como-resolver-divergências-entre-a-v02-aceita-e-os-caminhos-históricos).
3. **Validação:** [`uv run scripts/validate_conformance.py`](#verificação-local) valida o corpus golden; a CI executa o conjunto completo descrito em [CI](#ci).

## Status dos documentos

O README é o índice de autoridade. Ele não substitui os documentos técnicos; ele define o papel de cada um.

| Documento | Status | Papel |
|---|---|---|
| [`docs/PIBRAS-STANDARD-v0.2.md`](docs/PIBRAS-STANDARD-v0.2.md) | Normativo v0.2 (aceito) | Padrão vigente, aceito via PIBRAS-RFC-001. Fonte de verdade; preserva boas decisões da v0.1.0 técnica e corrige lacunas de governança, LGPD, autorização e conformidade. |
| [`docs/PROPERTY-STANDARD-v0.1.md`](docs/PROPERTY-STANDARD-v0.1.md) | Baseline técnica v0.1.0 (janela de compatibilidade) | Especificação técnica anterior, com as notas de transição para a v0.2. Em caso de conflito, a v0.2 prevalece. |
| [`docs/PIBRAS-STANDARD-v0.1.md`](docs/PIBRAS-STANDARD-v0.1.md) | Fundador / histórico | Consolidação original da visão, terminologia, manifesto e roadmap. Não decide conflitos técnicos. |
| [`docs/VERSIONING.md`](docs/VERSIONING.md) | Processo | Como versões, RFCs, compatibilidade e promoção de draft funcionam. |
| [`GOVERNANCE.md`](GOVERNANCE.md) | Governança | Papéis, autoridade de mudança e rito de publicação. |
| [`RFC_PROCESS.md`](RFC_PROCESS.md) | Processo | Como propor, revisar e aceitar mudanças normativas. |
| [`governance/release-policy.yaml`](governance/release-policy.yaml) | Governança | Política de release e fase atual (`legal_approved`). Validada por `scripts/validate_release_policy.py`. |
| [`docs/exposure-policy.md`](docs/exposure-policy.md) | Normativo v0.2 | Semântica de autorização e precedência `ExposurePolicy`. |
| [`docs/lgpd.md`](docs/lgpd.md) | Normativo v0.2 | Requisitos mínimos de LGPD, DSAR, retenção e auditoria. |
| [`docs/privacy-operations.md`](docs/privacy-operations.md) | Normativo v0.2 | Controles operacionais para fluxo de dados, enriquecimento, Sync Service, sharing ledger e gates de produção. |
| [`docs/lgpd-mitos-e-realidade.md`](docs/lgpd-mitos-e-realidade.md) | Guia interpretativo | Comparação detalhada entre mitos populares, realidade jurídica e controles operacionais da LGPD. |
| [`docs/entity-resolution.md`](docs/entity-resolution.md) | Normativo v0.2 | Regras de deduplicação, survivorship e revisão. |
| [`docs/vision/intermediacao-alto-padrao.md`](docs/vision/intermediacao-alto-padrao.md) | Informative Draft | Hipóteses sociotécnicas; não altera o core. |
| [`docs/profiles/high-end-brokerage-ux.md`](docs/profiles/high-end-brokerage-ux.md) | Application Profile Draft | Resultados de interação e privacidade; sem certificação. |
| [`docs/profiles/high-end-brokerage-implementation-matrix.md`](docs/profiles/high-end-brokerage-implementation-matrix.md) | Matriz informativa | Cobertura real e gaps; não declara paridade completa. |
| [`docs/rfcs/`](docs/rfcs/) | RFCs | [PIBRAS-RFC-001](docs/rfcs/accepted-001-v0.2-reconciliation.md) aceita (v0.2); drafts de Offer FSM, Money/Settlement e Presentation Context não atribuídas, sem efeito até aprovação. |
| [`mappings/v0.1.0-code-to-v0.2.md`](mappings/v0.1.0-code-to-v0.2.md) | Migração | De/Para entre artefatos atuais e o alvo v0.2. |
| [`docs/migrations/v0.1.0-to-v0.2.md`](docs/migrations/v0.1.0-to-v0.2.md) | Migração | Antes/depois por superfície (schema, tipos, DDL) na passagem v0.1.0 → v0.2. |
| [`docs/plans/v0.2-prontidao-publica.md`](docs/plans/v0.2-prontidao-publica.md) | Plano de execução (não normativo) | Frentes A01–A12 da v0.2 aceita até o candidato público. Não altera a norma. |
| [`LICENSE`](LICENSE) | Licenças | Apache-2.0 para código, schemas e artefatos técnicos ([`LICENSE-CODE`](LICENSE-CODE)); CC BY 4.0 para documentação ([`LICENSE-DOCS`](LICENSE-DOCS)). Mapa por caminho em [`licenses/APPLICABILITY.md`](licenses/APPLICABILITY.md). |

## Como resolver divergências entre a v0.2 aceita e os caminhos históricos

Ordem de autoridade para um consumidor:

1. **A v0.2 aceita prevalece.** `docs/PIBRAS-STANDARD-v0.2.md` e os documentos marcados como normativos v0.2 decidem conflitos. A v0.1 (fundadora) é contexto e a v0.1.0 técnica só vale como janela de compatibilidade ([`docs/VERSIONING.md`](docs/VERSIONING.md)).
2. **Os contratos legíveis por máquina implementam a v0.2.** `schema/mbras.schema.json`, `types/mbras.ts`, `db/schema.sql`, `openapi.yaml` e `tests/golden/` são validados por gates (veja [CI](#ci)). Se prosa e contrato divergirem, a norma v0.2 é a referência: trate a divergência como defeito do artefato ou, se exigir mudança normativa, siga [`RFC_PROCESS.md`](RFC_PROCESS.md).
3. **Os caminhos e nomes históricos são aliases de compatibilidade**, não fontes concorrentes:

| Histórico / compatibilidade | Alvo canônico v0.2 | Regra durante a janela v0.1.0 → v0.2 |
|---|---|---|
| `property.code`, `mb_code` | `external_ids[]` namespaced | `code` continua aceito; novos códigos de terceiros vão em `external_ids[]`. |
| `Owner`, `property_owners` | `Party`, `Ownership` | Permanecem compatíveis. A migração completa ainda está aberta (veja [Próximos passos](#próximos-passos)). |
| `Neighborhood` | `Geography` | `Neighborhood` permanece compatível; `Geography` é o alvo mais amplo. |
| `ExposureRule`, `field_visibility` | `ExposurePolicy` (default-deny) | Avalie `ExposurePolicy` primeiro; use `ExposureRule` apenas como fallback ([`docs/exposure-policy.md`](docs/exposure-policy.md)). |
| `schema/mbras.schema.json`, `types/mbras.ts` | Mesmos caminhos | Nomes preservados como caminhos de compatibilidade v1; o conteúdo implementa a v0.2. Não podem ser removidos antes da v2.0 (PIBRAS-RFC-001). |
| `docs/PROPERTY-STANDARD-v0.1.md` | `docs/PIBRAS-STANDARD-v0.2.md` | Consulte a v0.1.0 apenas para as notas de transição. |

Remoções só ocorrem em versão posterior, com migração documentada.

## Decisão de reconciliação v0.2

A v0.2 não apaga a baseline técnica anterior. Ela preserva:

- `Money` como `{ amount, currency }`, com `amount` em centavos;
- `Building -> Unit -> Property`, com `Unit` como identidade física durável e âncora de deduplicação;
- `ingestion_record` e `pending_change` como trilha bruta e fila de revisão;
- `field_visibility` como compatibilidade de leitura, migrando para `ExposurePolicy`.

Os artefatos técnicos já contêm os alvos de transição v0.2 para:

- `external_ids[]` namespaced para substituir `code`/`mb_code` como identificador canônico;
- `Organization` e `Tenant`;
- `Party` e `Ownership` como evolução de `Owner` e `property_owners`;
- `ExposurePolicy` com semântica default-deny;
- `DataSubjectRequest` para LGPD/DSAR;
- corpus de conformidade em `tests/golden/`.

## Arquivos técnicos

| Arquivo | O que é | Observação |
|---|---|---|
| [`docs/PROPERTY-STANDARD-v0.1.md`](docs/PROPERTY-STANDARD-v0.1.md) | Especificação técnica v0.1.0 + notas de transição v0.2 | Referência da janela de compatibilidade; em conflito, vale a v0.2. |
| [`schema/mbras.schema.json`](schema/mbras.schema.json) | JSON Schema draft 2020-12 com `$defs` (caminho de compatibilidade v1; nome preservado até v2.0) | Contrato formal de validação. |
| [`openapi.yaml`](openapi.yaml) | OpenAPI 3.1 mínimo | Superfície API-first de referência para Unit, Property, Listing, ExposurePolicy e conformidade. |
| [`types/mbras.ts`](types/mbras.ts) | Schemas Zod + tipos TypeScript inferidos (caminho de compatibilidade v1; nome preservado até v2.0) | Espelho de `schema/mbras.schema.json`. |
| [`db/schema.sql`](db/schema.sql) | DDL Postgres | Tabelas, histórico, governança, índices e read model. |
| [`examples/property.sample.json`](examples/property.sample.json) | Exemplo compatível v0.1.0 -> v0.2 | Mantém `code` e mostra `external_ids[]` durante a janela de transição. |
| [`tests/golden/`](tests/golden/) | Fixtures de conformidade | Casos mínimos para evitar divergência entre implementações. |
| [`tests/postgres/property_public.sql`](tests/postgres/property_public.sql) | Teste comportamental PostgreSQL | Verifica a projeção pública `property_public` (fail-closed) sobre o DDL aplicado. |

## Decisões que sustentam o modelo

1. **Property != Listing** — o ativo comercial é separado da exposição por canal.
2. **Unit != Property** — `Unit` é a identidade física durável; `Property` é o ciclo comercial.
3. **Proveniência em todo registro** — cada dado sabe origem, lote e `trust_tier`.
4. **Dados externos entram como sugestão** — fonte menos confiável não sobrescreve dado proprietário sem revisão.
5. **Autorização por política** — `ExposurePolicy` é o alvo v0.2; `ExposureRule` permanece como compatibilidade.
6. **LGPD por arquitetura** — controller/processor, finalidade, retenção e DSAR precisam existir como dados.
7. **Conformidade verificável** — fixtures golden complementam documentação e schemas; cada gate deve declarar seu escopo e não implica paridade exaustiva.

## Convenções atuais

Nomes `snake_case` · IDs `uuid` · instantes ISO 8601 UTC · dinheiro em centavos (`{ amount, currency }`) · áreas em m² · coordenadas WGS84.

Durante a janela de compatibilidade, `property.code` ainda existe para não quebrar consumidores. O alvo v0.2 é representar códigos de empresas em `external_ids[]`.

## Verificação local

As versões canônicas são Python `3.13.9`, uv `0.9.7`, Node `22.22.3` e npm `10.9.8`.
O estado Python é travado por `pyproject.toml` + `uv.lock`; o estado TypeScript é travado por `package.json` + `package-lock.json` v3.

Bootstrap reproduzível:

```bash
uv sync --frozen
npm ci
```

Checks canônicos do toolchain e dos contratos:

```bash
uv lock --check
uv run scripts/validate_conformance.py  # inclui exportação/round-trip schema.org
uv run scripts/validate_openapi.py
uv run openapi-spec-validator openapi.yaml
npm run typecheck
npm run test:types
npm run export:types-manifest -- --out .omo/evidence/task-2-types-manifest.json
scripts/qa/task-2.sh --report .omo/evidence/task-2-manifest.json
```

Gates adicionais que a CI também executa (veja [CI](#ci)):

```bash
uv run pytest
uv run scripts/check_contract_parity.py
uv run scripts/check_domain_invariants.py --entities tests/contracts/aligned/entities
uv run scripts/check_identity.py
uv run scripts/validate_release_policy.py governance/release-policy.yaml
uv run pip-audit
npm audit --audit-level=moderate
git ls-files -z | xargs -0 uv run detect-secrets-hook --baseline .secrets.baseline
```

DDL e teste comportamental em um PostgreSQL 16 descartável (a CI usa `postgres:16-alpine`, banco `pibras`, usuário `postgres`):

```bash
psql -h 127.0.0.1 -U postgres -d pibras -v ON_ERROR_STOP=1 -f db/schema.sql
psql -h 127.0.0.1 -U postgres -d pibras -v ON_ERROR_STOP=1 -f tests/postgres/property_public.sql
```

O segundo comando exige o primeiro já aplicado e termina com `ROLLBACK`, sem deixar dados. **Ele ainda não roda na CI** (veja [Próximos passos](#próximos-passos)).

Os validadores standalone continuam sendo executados via `uv run scripts/...`; não use chamadas diretas como `python3 scripts/validate_*.py`.

## CI

O workflow [`.github/workflows/ci.yml`](.github/workflows/ci.yml) roda em `pull_request` e em `push` para `main` e `release/**`, com dois jobs:

| Job (`name`) | Id | O que executa |
|---|---|---|
| `Conformance runner` | `conformance` | Instala só dependências de runtime (`uv sync --frozen --no-default-groups`) e roda `uv run --no-sync scripts/validate_conformance.py`. |
| `Contracts and reference DDL` | `contracts` | Instala `uv sync --frozen` e `npm ci`; roda `uv run pytest`, `npm run typecheck` e `npm run test:types`; valida contratos (conformidade, OpenAPI, `openapi-spec-validator`, paridade, invariantes de domínio); valida governança (`check_identity.py`, `validate_release_policy.py`); audita dependências e segredos (`pip-audit`, `npm audit --audit-level=moderate`, `detect-secrets-hook`); e aplica `db/schema.sql` em PostgreSQL 16. |

Diferenças conhecidas entre a CI e os comandos locais: `uv lock --check`, `npm run export:types-manifest` e `scripts/qa/task-2.sh` são checks locais e não rodam na CI; `tests/postgres/property_public.sql` também não.

## Próximos passos

1. ~~Fechar o De/Para em [`mappings/v0.1.0-code-to-v0.2.md`](mappings/v0.1.0-code-to-v0.2.md).~~ Concluído.
2. ~~Promover [`docs/PIBRAS-STANDARD-v0.2.md`](docs/PIBRAS-STANDARD-v0.2.md) via RFC.~~ Concluído: aceito via [PIBRAS-RFC-001](docs/rfcs/accepted-001-v0.2-reconciliation.md) (2026-08-21).
3. ~~Promover o runner de conformidade para CI.~~ Concluído: job `Conformance runner` (id `conformance`) em [`.github/workflows/ci.yml`](.github/workflows/ci.yml).
4. Completar a migração de `Owner` para `Party`/`Ownership` sem remover compatibilidade.
5. Integrar `tests/postgres/property_public.sql` à CI, após a aplicação do DDL.
6. Executar as frentes do [plano de prontidão pública v0.2](docs/plans/v0.2-prontidao-publica.md); a decisão de promoção cabe ao mantenedor, conforme [`docs/VERSIONING.md`](docs/VERSIONING.md) e `governance/release-policy.yaml`.
