# Golden tests de conformidade

Estes fixtures documentam comportamentos que implementações PIBRAS devem preservar. Casos JSON com `schema_ref` são envelopes de teste: o validador deve aplicar o schema ao campo `payload`.

## Fixtures

| Arquivo | Contrato |
|---|---|
| `money.centavos.expected.json` | Dinheiro canônico usa `{ amount, currency }`, com `amount` em centavos. |
| `property.valid.json` | `Property` aceita `external_ids[]` mantendo `code` na janela de compatibilidade. |
| `property.invalid-money.json` | Campos `_brl` escalares não são o formato monetário canônico. |
| `listing.public-masked.json` | Projeção pública mascara endereço e preço conforme política. |
| `portal-feed.valid.xml` | Feed de portal usa valores canônicos e política de endereço. |
| `import-row.pending-change.json` | Linha importada de fonte menos confiável gera `pending_change`. |
| `unit.duplicate-candidate.json` | Deduplicação usa `Unit` como âncora e registra score/decisão. |
| `exposure-policy.default-deny.json` | Campos sensíveis negam por padrão e só liberam por regra explícita. |
| `pending-change.external-overwrite.json` | Fonte menos confiável vira `pending_change`, não sobrescrita automática. |
| `data-subject-request.valid.json` | DSAR/LGPD exige tenant, tipo, status, prazo e trilha. |
| `schema-org.property-public.json` | Exportação schema.org usa somente a superfície pública e preserva os campos declarados no round-trip. |
| `schema-org.leaked-restricted-fields.invalid.json` | Exportador rejeita matrícula, coordenadas exatas e scores internos. |
| `schema-org.status-*.invalid.json` | Exportador rejeita estados que não podem ser publicados. |
| `conformance-cases.json` | Índice executável dos casos e de seus validadores especializados. |

## Verificação local

```bash
uv run scripts/validate_conformance.py
```

O runner valida envelopes com `schema_ref` contra `schema/mbras.schema.json`, garante que o índice `conformance-cases.json` aponte para fixtures rastreáveis, valida XML de portal, executa as decisões esperadas de `ExposurePolicy` e roda o exportador schema.org com round-trip e casos negativos.
