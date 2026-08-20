# Matriz de implementação — High-End Brokerage Profile

## Metadados

| Campo | Valor |
|---|---|
| Tipo | Matriz informativa de cobertura |
| Status | Draft |
| Efeito normativo | Nenhum |
| Data | 2026-08-20 |
| Finalidade | Rastreabilidade; não certificação |

## Como ler

- **Baseline vigente:** parte da baseline técnica atual.
- **Candidato v0.2:** implementado em alguma superfície, ainda não promovido.
- **Parcial/operacional:** cobertura incompleta ou não alinhada entre superfícies.
- **Ausente; depende de RFC:** não existe no core.
- **Bloqueado preventivamente:** trabalho retido até decisão externa.

Um gate verde prova somente as regras que ele implementa. `scripts/check_contract_parity.py` cobre seis classes de divergência (`PIBRAS-PAR-001` a `006`) e não prova paridade exaustiva de entidades, enums, tipos, nullability, defaults, FKs ou constraints.

## Matriz

| Capacidade | Estado atual | Evidência | Limites / próxima ação |
|---|---|---|---|
| `Building -> Unit -> Property -> Listing` | Baseline vigente | `types/mbras.ts`, `schema/mbras.schema.json`, `db/schema.sql` | `Unit.building_id` opcional é intencional. |
| Gates de paridade | Implementado com escopo limitado | `scripts/check_contract_parity.py` | As classes cobertas passam; não declarar “paridade completa”. |
| `Money { amount, currency }` | Parcial | DDL `BIGINT`; Zod `number().int()` | Definir limite safe integer e settlement via RFC. |
| Entity resolution | Candidato v0.2 alinhado | `docs/entity-resolution.md`, `src/dedupe/matcher.ts`, fixtures `unit.*` | Thresholds 0.95/0.75; validar desempenho com dados representativos. |
| Survivorship | Parcial/operacional | `src/survivorship/*`, `ingestion_record`, `pending_change` | Falta fluxo transacional e revisão ponta a ponta. |
| `ExposurePolicyEvaluator` | Parcial/operacional | `src/policy/evaluator.ts`, fixtures de política | `conditions` não são executadas no runtime; não alegar CBAC completo. |
| `property_public` | Limite estático endurecido | `db/schema.sql` | Consulta bases, exige listing público explícito e reduz geografia; política contextual permanece no engine. |
| schema.org P4a | Candidato executável | mapping, exporter e fixtures `schema-org.*` | Gate executa round-trip e negativos; não é modelo canônico. |
| RESO P4b | Bloqueado preventivamente | `mappings/reso-to-pibras.md` | Potencial incompatibilidade de licença requer revisão jurídica; candidatos não normativos. |
| Offer FSM | Ausente; depende de RFC | `offer` básico apenas no DDL | `docs/rfcs/draft-offer-fsm.md`. |
| Split settlement | Ausente; depende de RFC | Nenhum contrato core | `docs/rfcs/draft-money-settlement.md`. |
| Presentation Context / AST | Ausente; depende de RFC | Avaliador atual sem AST | `docs/rfcs/draft-presentation-context.md`. |
| Publicação como padrão aberto | Bloqueado por governança | `LICENSE`, `governance/release-policy.yaml` | Licença, RFC, revisão jurídica e release ainda pendentes. |

## Regra de atualização

Cada alteração deve citar o comando/teste que sustenta o novo status. Ausência de finding não deve ser convertida em cobertura não implementada pelo checker.
