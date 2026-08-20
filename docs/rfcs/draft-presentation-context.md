# RFC Draft: contexto de apresentação e condições de exposição

## Metadados

| Campo | Valor |
|---|---|
| RFC ID | Unassigned |
| Status | Draft; não normativo |
| Versão-alvo | Não agendada |
| Implementação | Limite público endurecido; AST/contexto não iniciados |
| Compatibilidade esperada | Aditiva para AST; potencialmente restritiva para publicação |
| Data | 2026-08-20 |
| Revisores | Nenhum registrado |

## Resumo

Propõe separar uma superfície pública estática, sempre minimizada, de projeções autenticadas e contextuais. Define requisitos para uma linguagem de condições fail-closed sem transformar falhas desconhecidas em permissões.

## Problema

`ExposurePolicyEvaluator` não executa `rule.conditions`. Uma view SQL sem parâmetros não conhece papel, finalidade, atribuição do broker ou modo de apresentação. A superfície pública anterior dependia de materialized view e podia devolver coordenadas exatas sob alias aproximado.

## Proposta

### Camadas

1. **`property_public`:** limite estático sobre tabelas base, listing explicitamente público, campos mínimos, geografia reduzida e sem política contextual.
2. **Policy engine autenticado:** avalia papel, ação, recurso, canal, finalidade, aprovações e condições.
3. **Projeção por canal/contexto:** serializa somente campos permitidos pela decisão corrente.
4. **RLS/grants:** impedem consumidores públicos de consultar superfícies internas.

Endereços continuam embutidos em `unit.addr_*` e `building.addr_*`; esta RFC não presume tabela `address`.

### Precisão geográfica

Arredondamento para duas casas é redução de precisão, não anonimização garantida. `address_display = hidden` deve omitir cidade/bairro/coordenadas e identificadores locacionais quando necessário. O policy engine pode exigir `neighborhood` ou `none`; nome do edifício e amenities também devem passar por avaliação de reidentificação.

### AST de condições

Compositores candidatos: `all`, `any`, `not`; predicados: `{ fact, operator, value }`. Fatos e operadores devem vir de allowlist versionada.

A avaliação é trivalorada:

```text
TRUE | FALSE | UNKNOWN
```

`UNKNOWN` nunca é convertido em `FALSE` antes de `not`. Qualquer `UNKNOWN` necessário para conceder `allow` impede a concessão e resulta em deny/fail-closed.

### Contexto de runtime

Candidatos: `public_feed`, `presentation`, `internal`. O contexto pertence à requisição de avaliação, não concede permissão por si só e não precisa ser persistido em `ExposurePolicy`.

### Precedência

A RFC final deve definir algoritmo por escopo e prioridade. Requisitos mínimos:

- deny explícito aplicável não pode ser ampliado por UI ou listing;
- ausência, ambiguidade, conflito ou erro resulta em deny;
- múltiplas políticas para o mesmo recurso devem ser rejeitadas ou resolvidas deterministicamente;
- overrides precisam de origem, validade e auditoria.

## Entidades e campos afetados

- `ExposureConditionAST` e allowlists em schema/Zod;
- `PolicyEvaluationContext` e evaluator;
- possível constraint de unicidade de política por recurso/tenant;
- fixtures de decisão e projeção;
- documentação da superfície `property_public`.

## Compatibilidade

A minimização pública é mudança restritiva intencional: consumidores que dependiam de listing com `exposure_level = NULL`, coordenada exata ou endereço oculto devem migrar. AST nova pode coexistir com conditions legadas apenas durante janela explícita; condition desconhecida nunca deve permitir.

## Segurança e LGPD

- política é reavaliada no momento da ação;
- aprovação não substitui policy;
- logs registram decisão, IDs e reason codes sem copiar payload sensível;
- caches e materialized views não podem prolongar autorização revogada;
- grants públicos sobre `property_full` são proibidos.

## Exemplos

```json
{
  "all": [
    { "fact": "broker_is_assigned", "operator": "eq", "value": true },
    { "fact": "presentation_mode", "operator": "eq", "value": "internal" }
  ]
}
```

Se `broker_is_assigned` não puder ser resolvido, o resultado é `UNKNOWN` e a regra não concede acesso, inclusive quando aninhada em `not`.

## Testes de conformidade

- revogação em tabela base remove imediatamente o registro público;
- listing `NULL`, restricted, confidential e off-market não entra na superfície pública;
- `hidden` remove geografia; outras modalidades nunca excedem duas casas;
- nenhuma coluna restrita integra a view;
- condição conhecida produz resultado esperado;
- condição desconhecida, erro e `not(UNKNOWN)` resultam em deny;
- deny prevalece nos empates definidos;
- payload não contém campos removidos, não apenas valores mascarados.

## Plano de migração

1. endurecer e testar a superfície pública estática;
2. inventariar conditions legadas;
3. definir allowlist de fatos/operadores e schema AST;
4. implementar evaluator trivalorado em paralelo;
5. adicionar fixtures e mutações de segurança;
6. migrar políticas e rejeitar conditions não reconhecidas;
7. promover somente após RFC aceita.

## Alternativas consideradas

- política integral em plain view: rejeitada por falta de contexto;
- `UNKNOWN = FALSE`: rejeitada porque `not(FALSE)` pode conceder acesso;
- CSS blur: rejeitado como controle de autorização;
- materialized public view: rejeitada para decisões revogáveis sem disciplina transacional de refresh.

## Questões abertas

- escopo e unicidade de políticas;
- conjunto inicial de fatos e operadores;
- representação de finalidade/aprovação;
- estratégia de RLS;
- política de reidentificação por nome do edifício e combinações de atributos.
