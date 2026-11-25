# RFC Draft: precisão monetária e liquidação de splits

## Metadados

| Campo | Valor |
|---|---|
| RFC ID | Unassigned |
| Status | Draft; não normativo |
| Versão-alvo | Não agendada |
| Implementação | Perfil optativo e função de referência de rateio disponíveis para ensaio |
| Compatibilidade esperada | Aditiva por adesão explícita ao perfil money-safe-v1 |
| Data | 2026-08-20 |
| Revisores | Nenhum registrado |

## Resumo

Propõe limite interoperável para `Money` em JSON/JavaScript e contratos separados para regra de split em negociação e liquidação final, conservando exatamente os centavos.

## Problema

A [norma v0.2](../PIBRAS-STANDARD-v0.2.md) exige valores na menor unidade monetária, mas não fixa um limite de magnitude no wire. O DDL usa `BIGINT`. Na implementação com Zod 4.6.7, `number().int()` rejeita `±9007199254740992` centavos; o JSON Schema aceita esses mesmos inteiros. Esses valores são representáveis como números binários, mas estão fora da faixa de inteiros seguros consecutivos do JavaScript.

Reprodução após instalação congelada: `uv run --frozen python scripts/check_semantic_parity.py`. A seção `compatibility_observations` registra os dois resultados de cada fronteira; não são casos de paridade aprovada. Mudança em qualquer resultado torna o gate vermelho para revisão. Essas observações continuam válidas para o contrato base.

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

O intervalo inclusivo acima vale para quem seleciona explicitamente [money-safe-v1](../../schema/profiles/money-safe-v1.json) ou importa [SafeMoney](../../types/profiles/money-safe-v1.ts). O perfil referencia a definição base e acrescenta limites ao campo `amount`. A forma JSON, as moedas aceitas e a validação v0.2 permanecem disponíveis. O PostgreSQL conserva `BIGINT`; na exportação pelo perfil, verificar a faixa **antes** de converter um inteiro ou decimal exato em JavaScript `number`. Reportar valores fora da faixa e preservar o registro original.

### Exportação decimal

Schema.org recebe `price` como texto decimal produzido por `Decimal(amount).scaleb(-2)`. Nenhum caminho pode converter o valor por `float`.

### Contratos candidatos

- `SplitRuleDraft`: linhas parciais, soma entre 0 e 10.000 bps.
- `SplitSettlement`: total não negativo, moeda única, soma exatamente 10.000 bps e valores materializados em centavos.
- A RFC final deve decidir se a mesma parte pode aparecer em múltiplos papéis; não se presume unicidade apenas por `recipient_party_id`.

### Distribuição de restos

1. calcular quociente inteiro e resto para cada linha;
2. distribuir centavos remanescentes pelos maiores restos;
3. desempatar pelo menor valor inteiro de `remainder_priority`, único no rateio;
4. registrar versão do algoritmo e regra aplicada;
5. garantir `sum(calculated_amount) = total_commission`.

A função de referência `allocateSettlement(total, linhas)` recebe um total em uma única moeda entre zero e o teto do perfil. Cada linha contém `bps` inteiro entre 0 e 10.000 e `remainder_priority` inteiro seguro. A função calcula produtos, quocientes e restos com `BigInt` e devolve uma quantia na moeda do total por linha, na ordem de entrada. A formalização das entidades de liquidação e sua persistência seguem em discussão.

## Compatibilidade

A adoção ocorre por interface de intercâmbio. Consumidores que selecionam a definição base continuam com o comportamento vigente. A promoção do perfil a requisito geral exige decisão normativa separada e avaliação dos dados legados.

## Segurança e LGPD

Recebedores, papéis e valores podem revelar relações profissionais e financeiras. A RFC final deve classificar campos, definir retenção, autorização, auditoria e minimização de exportações.

## Exemplos

Para 100 centavos e três linhas de 3333, 3333 e 3334 bps, o resultado deve somar exatamente 100. Empates usam `remainder_priority` imutável definida no acordo.

## Testes de conformidade

- mesmo corpus no JSON Schema e Zod do perfil, incluindo extremos inclusivos, primeiros valores externos, zero e frações;
- conversão centavos ↔ texto decimal sem `float`;
- rejeição de soma final diferente de 10.000;
- rejeição de bps negativos e prioridade duplicada;
- conservação para valores zero, grandes e distribuições periódicas;
- property-based tests com seed registrada, não apenas contagem de iterações;
- duas implementações produzem a mesma distribuição.

## Plano de migração

1. consultar máximos/mínimos monetários existentes;
2. decidir política para valores fora do intervalo;
3. selecionar o perfil apenas nas interfaces aderentes e executar os testes de fronteira;
4. adicionar entidades como experimental sem remover `Money` atual;
5. validar JSON Schema, Zod, DDL e PostgreSQL;
6. promover somente após RFC aceita.

## Alternativas consideradas

- string de centavos: preserva `int64`, mas quebra o wire atual;
- decimal major units: rejeitada como representação canônica por aumentar risco de escala;
- desempate por UUID: determinístico, mas sem precedência contratual e suscetível a viés arbitrário.

## Questões abertas

- regras de sinal para outros contextos além da liquidação ordinária;
- múltiplos papéis da mesma parte;
- modelo de estorno e correção;
- autoridade para definir `remainder_priority`;
- retenção e exposição de settlements.
