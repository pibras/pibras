# ExposurePolicy

`ExposurePolicy` é o alvo v0.2 para autorização de leitura, escrita, envio, exportação e publicação.

## Compatibilidade

`ExposureRule` permanece durante a janela v0.1.0 -> v0.2. Implementações novas devem avaliar `ExposurePolicy` primeiro e usar `ExposureRule` apenas como fallback de compatibilidade.

## Semântica

```txt
1. Campos sensíveis são default-deny.
2. Escrita, exportação, envio e publicação são default-deny.
3. Uma regra aplica quando `actions` contém a ação solicitada.
4. `fields` vazio cobre todos os campos; caso contrário, o match é exato ou por prefixo com ponto (`address` cobre `address.number`).
5. `roles` vazio cobre qualquer papel; caso contrário, o papel do sujeito deve estar listado.
6. `conditions` precisam ser satisfeitas antes de considerar a regra.
7. Cada regra pode declarar `priority` (inteiro, default 0); entre as regras que aplicam, a maior precedência vence.
8. No topo de prioridade empatado, deny explícito vence allow.
9. Sem regra aplicável, vale `default_decision` (default-deny), com reason_code `default_decision`.
10. Regra específica do recurso vence regra default.
11. A decisão needs_approval bloqueia a ação até aprovação.
12. Toda decisão retorna reason_code; `applied_rule_ids` é contrato de runtime (resultado da decisão), ainda não um campo do schema.
```

## Resultado esperado

```json
{
  "decision": "deny",
  "reason_code": "sensitive_field_default_deny",
  "applied_rule_ids": ["rule-id"],
  "masked_fields": ["address.number", "owner.tax_id"]
}
```

## Casos mínimos

- público lendo `address.number`: `deny`;
- broker responsável lendo `address.street`: `allow`;
- portal exportando `owner.tax_id`: `deny`;
- PDF privado sem aprovação: `needs_approval`.

## Verificação executável

O runner `scripts/validate_conformance.py` torna esta semântica testável: avalia as `expected_decisions` do fixture `tests/golden/exposure-policy.default-deny.json` (incluindo `priority`/empate e o ramo `default_decision`) e aplica o projetor de mascaramento sobre `projection_expectation` dos fixtures de listing, barrando vazamento de preço ou endereço.
