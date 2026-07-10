# Processo de RFC

Use RFC para mudanças que alterem entidades, campos, enums, política de segurança, LGPD, compatibilidade, feeds ou versionamento.

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

## Problema

## Proposta

## Entidades e campos afetados

## Compatibilidade

## Segurança e LGPD

## Exemplos

## Testes de conformidade

## Plano de migração
```

## Regras

- Nenhuma mudança de schema sem exemplo.
- Nenhuma mudança de segurança sem caso default-deny.
- Nenhuma mudança de ingestão sem regra de conflito.
- Nenhuma remoção sem janela de compatibilidade documentada.
