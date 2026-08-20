# Visão sociotécnica para aplicações de intermediação de alto padrão

## Metadados do documento

| Campo | Valor |
|---|---|
| Tipo | Visão informativa |
| Status | Informative Draft |
| Efeito normativo | Nenhum |
| Canônico | Não |
| Versão do documento | 0.1-draft |
| Base PIBRAS | Baseline v0.1.0; capacidades v0.2 identificadas por status |
| Data | 2026-08-20 |
| Editores | A designar |
| Revisores | Nenhum registrado |
| Licença | Pendente de aprovação jurídica |

## 1. Status e modo de leitura

Este documento apresenta hipóteses e cenários para aplicações de intermediação imobiliária que se identifiquem como operações de alto padrão. Ele não define faixa universal de preço, perfil psicológico de clientes, requisito jurídico ou contrato técnico do PIBRAS.

Afirmações sobre frequência, comportamento de mercado ou resultado comercial precisam de fonte identificável. Na ausência de fonte, devem ser lidas como **hipóteses de projeto a validar**, não como fatos empíricos.

## 2. Propósito

A visão ajuda implementadores a relacionar capacidades do PIBRAS a situações nas quais confidencialidade, singularidade do ativo, múltiplos intermediários e decisões sob pressão podem exigir controles adicionais. O padrão permanece independente de CRM, fornecedor, canal de comunicação, método de avaliação ou interface.

## 3. Terminologia e limites

- **Alto padrão:** rótulo de contexto declarado pelo implementador; não é classificação canônica do PIBRAS.
- **Intermediação:** contexto operacional entre participantes e recursos; não comprova representação, exclusividade ou validade contratual.
- **Off-market:** nível de exposição do domínio PIBRAS; não significa ausência de deveres legais ou autorização automática para compartilhamento privado.
- **UHNWI:** classificação de pessoas por patrimônio usada em estudos de mercado; não é tipo de imóvel nem entidade PIBRAS.

O Brasil não possui uma base nacional aberta, padronizada e cooperada equivalente a um MLS que forneça uniformemente preço de fechamento, atributos do ativo e histórico comercial. Registros cartoriais, fiscais e bases locais existem, mas não constituem por si só essa superfície interoperável.

## 4. Hipóteses sociotécnicas a validar

| ID | Hipótese | Evidência necessária |
|---|---|---|
| H1 | Canais informais podem fragmentar versões de preço, condições e autorização. | Pesquisa de campo e análise de incidentes. |
| H2 | Apresentações com terceiros ao lado do operador aumentam o risco de exposição visual. | Observação contextual e testes de uso. |
| H3 | Separar `Unit`, `Property` e `Listing` reduz duplicidade e mistura entre identidade física e exposição. | Testes de integração e dados reais anonimizados. |
| H4 | Revisão explícita antes de ações financeiras pode reduzir erros sem inviabilizar a tarefa. | Estudo de usabilidade e métricas de erro. |

## 5. Cadeia de riscos operacionais

- **D1 — Exposição indevida:** compartilhamento de endereço exato, dados de titularidade, documentos ou condições reservadas fora do canal autorizado.
- **D2 — Cacofonia de versões:** anúncios e mensagens divergentes sobre o mesmo ciclo comercial.
- **D3 — Perda de rastreabilidade:** propostas, contrapropostas e aprovações sem versão, prazo ou autoria verificável.
- **D4 — Memória organizacional frágil:** necessidades, objeções e decisões preservadas apenas em contas ou anotações individuais.

Esses riscos não são universais nem quantificados por este documento. Cada implementação deve validar ocorrência, impacto e prioridade no próprio contexto.

## 6. Participantes e proxy bias

Participantes possíveis incluem proprietário, comprador, corretor, gestor, backoffice, jurídico, controller, parceiro e operador de canal. O sistema não deve inferir que um corretor possui poderes irrestritos sobre decisões do proprietário. Relações operacionais não substituem instrumentos, manifestação de vontade ou verificação de poderes.

## 7. Princípios apoiados pelo PIBRAS

1. Separar identidade física, ciclo comercial e exposição: `Unit != Property != Listing`.
2. Avaliar autorização antes de leitura, publicação, exportação ou envio.
3. Minimizar payloads na origem; ocultação visual não amplia autorização.
4. Registrar proveniência e distinguir dado declarado, importado, inferido e calculado.
5. Tratar `needs_approval` como decisão pendente, não como permissão.
6. Preservar revisão humana em ações sensíveis.
7. Declarar cobertura parcial sem usar “paridade completa”.

## 8. Enquadramento jurídico limitado

Os Arts. 427 e 428 do Código Civil tratam da obrigatoriedade da proposta e de hipóteses em que ela deixa de ser obrigatória. Estados de software e timestamps podem apoiar rastreabilidade, mas não determinam sozinhos validade, recepção tempestiva, poderes de representação ou efeito jurídico.

O PIBRAS rejeita alegações de “conformidade jurídica nativa”. Modelos e controles podem facilitar governança; conformidade depende da operação, das partes, da finalidade e do caso concreto.

## 9. Não objetivos

- definir score obrigatório de cliente, qualidade, raridade ou liquidez;
- prescrever telas, cores, número de cliques ou stack;
- substituir avaliação jurídica, contrato ou assinatura;
- prometer aumento de conversão ou redução de litígio;
- declarar equivalência integral com RESO, schema.org ou qualquer sistema externo.

## 10. Relação com outros documentos

- Contratos vigentes e status: [`README.md`](../../README.md).
- Autorização: [`docs/exposure-policy.md`](../exposure-policy.md).
- Privacidade operacional: [`docs/privacy-operations.md`](../privacy-operations.md).
- Perfil de aplicação: [`docs/profiles/high-end-brokerage-ux.md`](../profiles/high-end-brokerage-ux.md).
- Matriz de implementação: [`docs/profiles/high-end-brokerage-implementation-matrix.md`](../profiles/high-end-brokerage-implementation-matrix.md).
