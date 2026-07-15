# LGPD no PIBRAS

Este documento descreve como as entidades do padrão suportam conformidade. Os requisitos
operacionais, a taxonomia **MUST / POLICY-SHALL / SHOULD / MAY**, o Sync Service e os gates
de compartilhamento estão em [`privacy-operations.md`](privacy-operations.md). Em caso de
conflito, a lei e a regulamentação aplicável prevalecem; entre documentos PIBRAS, o requisito
mais restritivo prevalece até reconciliação por RFC.

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

Campos pessoais ou de risco elevado são marcados no `schema/mbras.schema.json` com `x-pii: true` e `x-sensitivity` (ex.: `Owner.tax_id`, `Party.tax_id`, `Property.min_accepted_price`). `x-sensitivity` é classificação de risco do PIBRAS, não declaração de que todo campo marcado é "dado pessoal sensível" na definição do art. 5º, II, da LGPD. A lista operacional (draft §7.1) deve derivar dessas anotações, não de prosa paralela.

## Regra de implementação

Dados pessoais sensíveis não devem depender de ocultação no frontend. A API deve aplicar `ExposurePolicy` antes de retornar ou exportar campos.

## Referências oficiais

- [Lei nº 13.709/2018 — LGPD](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm)
- [Publicações e guias da ANPD](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes)
