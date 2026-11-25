# RFC Draft: precisão monetária e liquidação de splits

## Metadados

| Campo | Valor |
|---|---|
| RFC ID | Unassigned |
| Status | Draft; não normativo |
| Versão-alvo | Não agendada |
| Implementação | Correção Decimal no exporter; settlement não iniciado |
| Compatibilidade esperada | Aditiva, exceto novos limites de `Money` |
| Data | 2026-08-20 |
| Revisores | Nenhum registrado |

## Resumo

Propõe limite interoperável para `Money` em JSON/JavaScript e contratos separados para regra de split em negociação e liquidação final, conservando exatamente os centavos.

## Problema

A [norma v0.2](../PIBRAS-STANDARD-v0.2.md) exige valores na menor unidade monetária, mas não fixa um limite de magnitude no wire. O DDL usa `BIGINT`. Na implementação com Zod 4.6.7, `number().int()` rejeita `±9007199254740992` centavos; o JSON Schema aceita esses mesmos inteiros. Esses valores são representáveis como números binários, mas estão fora da faixa de inteiros seguros consecutivos do JavaScript.

Reprodução após instalação congelada: `uv run --frozen python scripts/check_semantic_parity.py`. A seção `compatibility_observations` registra os dois resultados de cada fronteira; não são casos de paridade aprovada. Mudança em qualquer resultado torna o gate vermelho para revisão. **Antes da promoção**, o mantenedor deve decidir a faixa interoperável via RFC e a estratégia de compatibilidade; este ensaio não autoriza restringir o schema nem relaxar o SDK.

O core não possui `SplitRuleDraft` nem `SplitSettlement`. Exportadores não devem converter centavos por ponto flutuante binário.

## Proposta

### Money no wire

Manter o shape atual:

```json
{ "amount": 1750000000, "currency": "BRL" }
```

`amount` deve estar no intervalo signed safe integer de JavaScript:

```text
-9007199254740991 <= amount <= 9007199254740991
```

JSON Schema deve declarar `minimum`/`maximum`; Zod deve usar validação safe; o DDL deve aplicar `CHECK` equivalente ou documentar que a superfície de wire é mais estreita que `BIGINT`. “Exato” significa representável por runtimes JavaScript dentro desse intervalo, não propriedade universal de todo parser JSON.

### Exportação decimal

Schema.org recebe `price` como texto decimal produzido por `Decimal(amount).scaleb(-2)`. Nenhum caminho pode converter o valor por `float`.

### Contratos candidatos

- `SplitRuleDraft`: linhas parciais, soma entre 0 e 10.000 bps.
- `SplitSettlement`: total não negativo, moeda única, soma exatamente 10.000 bps e valores materializados em centavos.
- A RFC final deve decidir se a mesma parte pode aparecer em múltiplos papéis; não se presume unicidade apenas por `recipient_party_id`.

### Distribuição de restos

1. calcular quociente inteiro e resto para cada linha;
2. distribuir centavos remanescentes pelos maiores restos;
3. desempatar por `remainder_priority` contratual explícita e única, não por UUID;
4. registrar versão do algoritmo e regra aplicada;
5. garantir `sum(calculated_amount) = total_commission`.

## Entidades e campos afetados

- limites de `Money` em schema, Zod e DDL;
- novos `SplitRuleDraft`, `SplitSettlement` e linhas associadas;
- enums de papel ainda a decidir;
- exporter schema.org e fixtures monetárias;
- OpenAPI se as entidades forem expostas.

## Compatibilidade

Adicionar limites pode rejeitar valores anteriormente aceitos. A promoção depende de auditoria demonstrando que dados existentes estão dentro do intervalo ou de migração explícita. As entidades de split são aditivas, mas seus enums também afetam consumidores fechados.

## Segurança e LGPD

Recebedores, papéis e valores podem revelar relações profissionais e financeiras. A RFC final deve classificar campos, definir retenção, autorização, auditoria e minimização de exportações.

## Exemplos

Para 100 centavos e três linhas de 3333, 3333 e 3334 bps, o resultado deve somar exatamente 100. Empates usam `remainder_priority` imutável definida no acordo.

## Testes de conformidade

- limites safe integer aceitos/rejeitados nas três superfícies;
- conversão centavos ↔ texto decimal sem `float`;
- rejeição de soma final diferente de 10.000;
- rejeição de bps negativos e prioridade duplicada;
- conservação para valores zero, grandes e distribuições periódicas;
- property-based tests com seed registrada, não apenas contagem de iterações;
- duas implementações produzem a mesma distribuição.

## Plano de migração

1. consultar máximos/mínimos monetários existentes;
2. decidir política para valores fora do intervalo;
3. adicionar bounds e fixtures de fronteira;
4. adicionar entidades como experimental sem remover `Money` atual;
5. validar JSON Schema, Zod, DDL e PostgreSQL;
6. promover somente após RFC aceita.

## Alternativas consideradas

- string de centavos: preserva `int64`, mas quebra o wire atual;
- decimal major units: rejeitada como representação canônica por aumentar risco de escala;
- desempate por UUID: determinístico, mas sem precedência contratual e suscetível a viés arbitrário.

## Questões abertas

- limites negativos por contexto;
- múltiplos papéis da mesma parte;
- modelo de estorno e correção;
- autoridade para definir `remainder_priority`;
- retenção e exposição de settlements.
