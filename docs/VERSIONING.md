# Versionamento do PIBRAS

## Estados dos documentos

| Estado | Significado | Pode orientar implementação? |
|---|---|---|
| Fundador / histórico | Registra a visão original e decisões que explicam o projeto. | Sim, para contexto. Não decide conflitos técnicos. |
| Baseline técnica | Define os artefatos atuais que devem continuar validando. | Sim, é a fonte de verdade da versão publicada. |
| Draft de reconciliação | Propõe mudanças e migrações para a próxima versão. | Sim, apenas quando o De/Para explicita compatibilidade. |
| Aceito | Draft aprovado por RFC e refletido em docs, schema, tipos, DDL, exemplos e testes. | Sim, passa a ser o padrão vigente. |

## Versões atuais

| Versão | Status | Arquivos |
|---|---|---|
| v0.1 | Fundador / histórico | `docs/PIBRAS-STANDARD-v0.1.md` |
| v0.1.0 | Baseline técnica atual | `docs/PROPERTY-STANDARD-v0.1.md`, `schema/mbras.schema.json`, `types/mbras.ts`, `db/schema.sql`, `examples/property.sample.json` |
| v0.2 | Draft de reconciliação | `docs/PIBRAS-STANDARD-v0.2-draft.md`, `mappings/v0.1.0-code-to-v0.2.md`, `openapi.yaml` |

## Regra de promoção

Um draft só vira padrão aceito quando todos os itens abaixo existem:

```txt
1. RFC aprovada.
2. README atualizado.
3. De/Para completo para campos e entidades afetadas.
4. JSON Schema atualizado.
5. Tipos Zod/TypeScript atualizados.
6. DDL Postgres atualizado.
7. Exemplos positivos atualizados.
8. Exemplos negativos ou golden tests adicionados.
9. Comando de verificação documentado e executado (`uv run scripts/validate_conformance.py`).
10. OpenAPI validado quando a mudança afetar superfície de API.
```

## Política de compatibilidade

Durante a janela v0.1.0 -> v0.2:

- `property.code` permanece aceito como alias de compatibilidade.
- `external_ids[]` é o alvo canônico para códigos de terceiros.
- `Owner` e `property_owners` permanecem compatíveis.
- `Party` e `Ownership` são o alvo canônico.
- `Neighborhood` permanece compatível.
- `Geography` é o alvo canônico mais amplo.
- `ExposureRule` permanece compatível.
- `ExposurePolicy` é o alvo canônico para decisão de autorização.
- `ingestion_record` e `pending_change` continuam como trilhas operacionais.
- `ImportSource`, `ImportBatch` e `ImportMapping` entram como metadados de orquestração.
- O runner de conformidade em `scripts/validate_conformance.py` é obrigatório para promover fixtures golden.

Remoções só podem acontecer em uma versão posterior com migração documentada.

## Versionamento semântico

```txt
MAJOR: quebra consumidores ou remove compatibilidade.
MINOR: adiciona entidades, campos opcionais, mappings ou políticas compatíveis.
PATCH: corrige documentação, exemplos, enums ou validações sem mudar contrato.
```

Enquanto o projeto está abaixo de `1.0.0`, toda mudança ainda precisa declarar impacto de compatibilidade.
