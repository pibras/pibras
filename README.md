# PIBRAS — Portfólio Imobiliário do Brasil

Camada e padrão aberto para organizar, importar, normalizar, governar e distribuir dados imobiliários no Brasil.

**PIBRAS é o padrão; a stack é apenas uma forma de implementar.**

## Status dos documentos

O README é o índice de autoridade. Ele não substitui os documentos técnicos; ele define o papel de cada um.

| Documento | Status | Papel |
|---|---|---|
| [`docs/PIBRAS-STANDARD-v0.1.md`](docs/PIBRAS-STANDARD-v0.1.md) | Fundador / histórico | Consolidação original da visão, terminologia, manifesto e roadmap. Não é mais a fonte única para decisões técnicas. |
| [`docs/PROPERTY-STANDARD-v0.1.md`](docs/PROPERTY-STANDARD-v0.1.md) | Baseline técnica v0.1.0 | Fonte de verdade dos artefatos atuais em `schema/`, `types/`, `db/` e `examples/`. |
| [`docs/PIBRAS-STANDARD-v0.2.md`](docs/PIBRAS-STANDARD-v0.2.md) | Normativo v0.2 (aceito) | Padrão vigente, aceito via PIBRAS-RFC-001. Fonte de verdade; preserva boas decisões da v0.1.0 técnica e corrige lacunas de governança, LGPD, autorização e conformidade. |
| [`docs/VERSIONING.md`](docs/VERSIONING.md) | Processo | Como versões, RFCs, compatibilidade e promoção de draft funcionam. |
| [`GOVERNANCE.md`](GOVERNANCE.md) | Governança | Papéis, autoridade de mudança e rito de publicação. |
| [`RFC_PROCESS.md`](RFC_PROCESS.md) | Processo | Como propor, revisar e aceitar mudanças normativas. |
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

## Decisão de reconciliação v0.2

A v0.2 não deve apagar a baseline técnica atual. Ela deve preservar:

- `Money` como `{ amount, currency }`, com `amount` em centavos;
- `Building -> Unit -> Property`, com `Unit` como identidade física durável e âncora de deduplicação;
- `ingestion_record` e `pending_change` como trilha bruta e fila de revisão;
- `field_visibility` como compatibilidade de leitura, migrando para `ExposurePolicy`.

A baseline técnica já contém os alvos de transição v0.2 para:

- `external_ids[]` namespaced para substituir `code`/`mb_code` como identificador canônico;
- `Organization` e `Tenant`;
- `Party` e `Ownership` como evolução de `Owner` e `property_owners`;
- `ExposurePolicy` com semântica default-deny;
- `DataSubjectRequest` para LGPD/DSAR;
- corpus de conformidade em `tests/golden/`.

## Arquivos técnicos

| Arquivo | O que é | Observação |
|---|---|---|
| [`docs/PROPERTY-STANDARD-v0.1.md`](docs/PROPERTY-STANDARD-v0.1.md) | Especificação técnica v0.1.0 + notas de transição v0.2 | Atualizar junto com schema, tipos e DDL. |
| [`schema/mbras.schema.json`](schema/mbras.schema.json) | JSON Schema draft 2020-12 com `$defs` (caminho de compatibilidade v1; nome preservado até v2.0) | Contrato formal de validação. |
| [`openapi.yaml`](openapi.yaml) | OpenAPI 3.1 mínimo | Superfície API-first de referência para Unit, Property, Listing, ExposurePolicy e conformidade. |
| [`types/mbras.ts`](types/mbras.ts) | Schemas Zod + tipos TypeScript inferidos (caminho de compatibilidade v1; nome preservado até v2.0) | Espelho de `schema/mbras.schema.json`. |
| [`db/schema.sql`](db/schema.sql) | DDL Postgres | Tabelas, histórico, governança, índices e read model. |
| [`examples/property.sample.json`](examples/property.sample.json) | Exemplo compatível v0.1.0 -> v0.2 | Mantém `code` e mostra `external_ids[]` durante a janela de transição. |
| [`tests/golden/`](tests/golden/) | Fixtures de conformidade | Casos mínimos para evitar divergência entre implementações. |

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

Checks canônicos:

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

Os validadores standalone continuam sendo executados via `uv run scripts/...`; não use chamadas diretas como `python3 scripts/validate_*.py`.

## Próximos passos

1. ~~Fechar o De/Para em [`mappings/v0.1.0-code-to-v0.2.md`](mappings/v0.1.0-code-to-v0.2.md).~~ Concluído.
2. ~~Promover [`docs/PIBRAS-STANDARD-v0.2.md`](docs/PIBRAS-STANDARD-v0.2.md) via RFC.~~ Concluído: aceito via [PIBRAS-RFC-001](docs/rfcs/accepted-001-v0.2-reconciliation.md) (2026-08-21).
3. Completar a migração de `Owner` para `Party`/`Ownership` sem remover compatibilidade.
4. Promover o runner de conformidade para CI.
