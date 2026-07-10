# LGPD no PIBRAS

## Requisitos mínimos v0.2

- `Tenant` identifica o limite operacional de dados.
- `Organization` identifica operadores e patrocinadores institucionais.
- `Party` concentra dados pessoais de pessoas e organizações.
- `RetentionPolicy` define prazo de retenção e ação na expiração (`delete`, `anonymize`, `review`, `archive`); `Tenant` e `Party` referenciam-na por `retention_policy_id`.
- `DataSubjectRequest` registra solicitações de titular, com efeito concreto da resolução (`resolution_action` + `affected_record_ids`).
- `ExposurePolicy` limita leitura, envio, exportação e publicação.

## Controlador, operador e suboperador

Cada tenant deve declarar:

- controlador dos dados;
- operador dos dados;
- suboperadores relevantes;
- finalidade de tratamento;
- base legal;
- retenção;
- permissão de transferência internacional.

## DSAR

Solicitações de acesso, correção, exclusão, portabilidade e oposição devem ser registradas como `DataSubjectRequest`, com prazo (`due_at`), status e trilha de auditoria. Numa exclusão cumprida, `resolution_action` (ex.: `anonymize`) e `affected_record_ids` registram o efeito concreto aplicado, alinhado à `RetentionPolicy` do tenant. Ver fixture `tests/golden/data-subject-request.deletion-fulfilled.json`.

## Classificação de PII

Campos sensíveis são marcados no `schema/mbras.schema.json` com `x-pii: true` e `x-sensitivity` (ex.: `Owner.tax_id`, `Party.tax_id`, `Property.min_accepted_price`). A lista normativa de dados sensíveis (draft §7.1) deve derivar dessas anotações, não de prosa paralela.

## Regra de implementação

Dados pessoais sensíveis não devem depender de ocultação no frontend. A API deve aplicar `ExposurePolicy` antes de retornar ou exportar campos.
