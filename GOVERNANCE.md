# Governança do PIBRAS

O PIBRAS deve operar como padrão aberto, não como vocabulário fechado de uma única empresa.

## Papéis

| Papel | Responsabilidade |
|---|---|
| Sponsor inicial | Financia e fornece casos reais de uso. |
| Maintainers | Revisam RFCs, compatibilidade, schemas e releases. |
| Working Group | Discute mudanças de padrão, integração, LGPD e adoção. |
| Implementadores | Validam o padrão em CRMs, portais, sites, APIs e ferramentas internas. |

## Regra institucional

Os patrocinadores fundadores podem ser primeiros casos de uso, mas o vocabulário público vive sob a organização neutra Ibvi (`https://pibras.ibvi.ai`, repositório `https://github.com/ibvi-br/pibras.git`) antes de lançamento externo. Decisão registrada em `governance/release-policy.yaml` (aprovador: Ronaldo, 2026-07-10).

## Critérios para aceitar mudança

Uma mudança no padrão precisa:

- declarar problema e motivação;
- listar impacto em compatibilidade;
- atualizar docs, schemas, tipos, DDL e exemplos quando aplicável;
- incluir ou atualizar golden tests;
- informar impacto de LGPD e segurança;
- documentar migração.

## Licença recomendada

- Código, schemas e SDKs: Apache-2.0.
- Documentação e especificação: CC BY 4.0.

As licenças finais devem ser revisadas juridicamente antes de publicação pública.
