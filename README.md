# PIBRAS — Portfólio Imobiliário do Brasil

Camada e padrão aberto para organizar, importar, normalizar, governar e distribuir dados imobiliários no Brasil.

**PIBRAS é o padrão; a stack é apenas uma forma de implementar.**

## Status dos documentos

O README é o índice de autoridade. Ele não substitui os documentos técnicos; ele define o papel de cada um.

| Documento | Status | Papel |
|---|---|---|
| [`docs/PIBRAS-STANDARD-v0.1.md`](docs/PIBRAS-STANDARD-v0.1.md) | Fundador / histórico | Consolidação original da visão, terminologia, manifesto e roadmap. Não é mais a fonte única para decisões técnicas. |
| [`docs/MBRAS-PROPERTY-STANDARD.md`](docs/MBRAS-PROPERTY-STANDARD.md) | Baseline técnica v0.1.0 | Fonte de verdade dos artefatos atuais em `schema/`, `types/`, `db/` e `examples/`. |
| [`docs/PIBRAS-STANDARD-v0.2-draft.md`](docs/PIBRAS-STANDARD-v0.2-draft.md) | Draft de reconciliação | Próximo padrão proposto. Preserva boas decisões da v0.1.0 técnica e corrige lacunas de governança, LGPD, autorização e conformidade. |
| [`docs/VERSIONING.md`](docs/VERSIONING.md) | Processo | Como versões, RFCs, compatibilidade e promoção de draft funcionam. |
| [`GOVERNANCE.md`](GOVERNANCE.md) | Governança | Papéis, autoridade de mudança e rito de publicação. |
| [`RFC_PROCESS.md`](RFC_PROCESS.md) | Processo | Como propor, revisar e aceitar mudanças normativas. |
| [`docs/exposure-policy.md`](docs/exposure-policy.md) | Normativo v0.2 | Semântica de autorização e precedência `ExposurePolicy`. |
| [`docs/lgpd.md`](docs/lgpd.md) | Normativo v0.2 | Requisitos mínimos de LGPD, DSAR, retenção e auditoria. |
| [`docs/entity-resolution.md`](docs/entity-resolution.md) | Normativo v0.2 | Regras de deduplicação, survivorship e revisão. |
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
| [`docs/MBRAS-PROPERTY-STANDARD.md`](docs/MBRAS-PROPERTY-STANDARD.md) | Especificação técnica v0.1.0 + notas de transição v0.2 | Atualizar junto com schema, tipos e DDL. |
| [`schema/mbras.schema.json`](schema/mbras.schema.json) | JSON Schema draft 2020-12 com `$defs` | Contrato formal de validação. |
| [`openapi.yaml`](openapi.yaml) | OpenAPI 3.1 mínimo | Superfície API-first de referência para Unit, Property, Listing, ExposurePolicy e conformidade. |
| [`types/mbras.ts`](types/mbras.ts) | Schemas Zod + tipos TypeScript inferidos | Espelho de `schema/mbras.schema.json`. |
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
7. **Conformidade verificável** — fixtures golden complementam documentação e schemas.

## Convenções atuais

Nomes `snake_case` · IDs `uuid` · instantes ISO 8601 UTC · dinheiro em centavos (`{ amount, currency }`) · áreas em m² · coordenadas WGS84.

Durante a janela de compatibilidade, `property.code` ainda existe para não quebrar consumidores. O alvo v0.2 é representar códigos de empresas em `external_ids[]`.

## Verificação local

Não há `package.json` neste repositório. O runner de conformidade usa `uv` e valida JSON Schema draft 2020-12, XML de portal, índice de casos e expectativas de `ExposurePolicy`:

```bash
uv run scripts/validate_conformance.py && uv run scripts/validate_openapi.py
```

## Próximos passos

1. Fechar o De/Para em [`mappings/v0.1.0-code-to-v0.2.md`](mappings/v0.1.0-code-to-v0.2.md).
2. Promover ou ajustar [`docs/PIBRAS-STANDARD-v0.2-draft.md`](docs/PIBRAS-STANDARD-v0.2-draft.md) via RFC.
3. Completar a migração de `Owner` para `Party`/`Ownership` sem remover compatibilidade.
4. Promover o runner de conformidade para CI.
