# Alterações do PIBRAS

## v0.2.0 — candidata à promoção (não publicada)

- A titularidade legada pode ser projetada em Party e Ownership com recibo de reversão e verificação de conflito. A projeção de compatibilidade conserva o vínculo ao imóvel.
- O contrato de titularidade exige exatamente um alvo, imóvel ou unidade. O DDL verifica a coerência entre unidade e edifício.
- O OpenAPI distingue operações servidas das operações especificadas para implementações. O conjunto de conformidade inclui cenários HTTP, paridade de aceitação e testes comportamentais em PostgreSQL 16.
- O contrato base de `Money` permanece inalterado: o JSON Schema não impõe o limite de inteiro seguro do JavaScript, e o Zod da implementação de referência rejeita valores fora dessa faixa.
- O perfil **optativo** `money-safe-v1` limita o intercâmbio a centavos inteiros de −9.007.199.254.740.991 a +9.007.199.254.740.991, inclusive. Em JavaScript, use `parseSafeMoneyJson(raw)` sobre o texto original para evitar arredondamento antes da validação.
- A [RFC Money/Settlement](docs/rfcs/draft-money-settlement.md) continua **draft**. A função de rateio é referência experimental, não requisito de conformidade da v0.2.0.
- O kit de ensaio registra as versões dos componentes, as licenças e o commit de origem. A política de release registra a fase de promoção aplicável.
