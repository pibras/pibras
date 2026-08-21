# Processo de RFC

Use RFC para mudanças que alterem entidades, campos, enums, política de segurança, LGPD, compatibilidade, feeds ou versionamento.

## Estados

| Estado | Efeito |
|---|---|
| Draft | Proposta sem ID atribuído e sem efeito normativo. |
| Review | ID atribuído; em deliberação pública/técnica. |
| Accepted | Aprovada pelos mantenedores e refletida em todos os artefatos aplicáveis. |
| Rejected | Encerrada sem alteração do padrão. |
| Superseded | Substituída por RFC posterior identificada. |

Arquivos em `docs/rfcs/draft-*.md` permanecem `Draft` e usam `RFC ID: Unassigned` até registro formal pelos mantenedores. Criar o arquivo não equivale a submeter, aceitar ou implementar a proposta.

## Registro de drafts atuais

| Draft | Status | Efeito atual |
|---|---|---|
| [`docs/rfcs/draft-offer-fsm.md`](docs/rfcs/draft-offer-fsm.md) | Draft / Unassigned | Nenhum |
| [`docs/rfcs/draft-money-settlement.md`](docs/rfcs/draft-money-settlement.md) | Draft / Unassigned | Nenhum |
| [`docs/rfcs/draft-presentation-context.md`](docs/rfcs/draft-presentation-context.md) | Draft / Unassigned | Nenhum |
| [`docs/rfcs/draft-v0.2-reconciliation.md`](docs/rfcs/draft-v0.2-reconciliation.md) | Draft / Unassigned | Nenhum |

## Fluxo

```txt
1. Abrir proposta
2. Explicar problema
3. Descrever mudança
4. Listar impacto em compatibilidade
5. Adicionar exemplos antes/depois
6. Atualizar De/Para quando houver migração
7. Adicionar ou atualizar golden tests
8. Revisar LGPD e segurança
9. Aprovar ou rejeitar
10. Publicar release notes
```

## Template

```md
# RFC: <titulo>

## Metadados
## Resumo
## Problema

## Proposta

## Entidades e campos afetados

## Compatibilidade

## Segurança e LGPD

## Exemplos

## Testes de conformidade

## Plano de migração
## Alternativas consideradas
## Questões abertas
```

## Regras

- Nenhuma mudança de schema sem exemplo.
- Nenhuma mudança de segurança sem caso default-deny.
- Nenhuma mudança de ingestão sem regra de conflito.
- Nenhuma remoção sem janela de compatibilidade documentada.
