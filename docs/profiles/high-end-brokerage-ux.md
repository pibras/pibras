# High-End Brokerage UX Application Profile

## Metadados do documento

| Campo | Valor |
|---|---|
| Tipo | Application Profile |
| Status | Draft experimental |
| Efeito sobre o PIBRAS Core | Nenhum |
| Conformidade | Autodeclaração de cobertura; sem certificação |
| Versão | 0.1-draft |
| Data | 2026-08-20 |
| Revisores | Nenhum registrado |
| Licença | Pendente de aprovação jurídica |

## 1. Aplicabilidade

Este perfil descreve resultados observáveis de privacidade, autorização e interação para clientes que consomem PIBRAS. Não é design system e não torna extensões locais canônicas. Os termos normativos abaixo valem somente para quem declarar conformidade com **este perfil draft**.

- **REQUIRED:** condição mínima do perfil.
- **RECOMMENDED:** prática preferida, justificável por exceção documentada.
- **EXPERIMENTAL:** mecanismo sujeito a teste.
- **RESEARCH HYPOTHESIS:** hipótese sem força de conformidade.

## 2. Autoridade e entidades

O perfil reutiliza `Organization`, `Tenant`, `User`, `Party`, `Broker`, `Building`, `Unit`, `Property`, `Listing`, `MediaAsset`, `Document`, `PublicationChannel` e `ExposurePolicy` respeitando o status de cada superfície. `Offer` existe apenas como capacidade operacional parcial no DDL; estados adicionais dependem de RFC.

`PropertyDraft` significa somente rascunho local de uma futura submissão e **não é entidade canônica PIBRAS**.

## 3. Privacidade social e minimização

- **[REQUIRED]** A autorização deve ser avaliada no backend antes da serialização. CSS `blur`, `opacity`, `display: none` ou remoção tardia do DOM não são controles de autorização.
- **[REQUIRED]** Dados retidos por política não devem existir no payload entregue ao contexto de apresentação.
- **[REQUIRED]** Falha de sessão, papel, contexto ou política deve resultar em `deny`/projeção mais restritiva.
- **[REQUIRED]** A interface deve distinguir valor desconhecido, não aplicável, retido por política e pendente de aprovação.
- **[REQUIRED]** Nenhuma condição da interface pode ampliar a autorização concedida pelo servidor.

## 4. Estados de transporte e domínio

- **[REQUIRED]** Estados locais de transporte devem ser separados do estado de negócio:

```text
UI/transporte: draft_local -> queued -> transmitting -> acknowledged | failed
Oferta vigente no DDL: submitted | countered | accepted | rejected | withdrawn
Estados futuros: somente após aprovação de RFC
```

`acknowledged` confirma recepção técnica; não significa aceite comercial ou efeito jurídico. Uma operação retida localmente nunca deve aparecer como submetida ao servidor.

## 5. Cache local

- **[REQUIRED]** Cache local deve ser minimizado, isolado por usuário/tenant, revogável e possuir expiração compatível com finalidade e sensibilidade.
- **[REQUIRED]** Segredos, documentos de titularidade e `min_accepted_price` não devem ser persistidos localmente sem necessidade aprovada e controle específico.
- **[RECOMMENDED]** Usar proteção de chave e criptografia em repouso quando suportadas pela plataforma e pelo baseline criptográfico da implementação.
- **[RECOMMENDED]** Limpar rascunhos após sincronização, logout, revogação ou expiração da finalidade.

Este perfil não impõe algoritmo, produto de banco, TTL universal ou suporte biométrico. Controles concretos dependem do threat model e da plataforma.

## 6. Ações críticas

- **[REQUIRED]** Antes de enviar valor ou condição comercial, apresentar resumo inequívoco e exigir confirmação explícita, acessível e não acidental.
- **[REQUIRED]** A confirmação deve respeitar locale e moeda; texto por extenso é opcional e não substitui o valor canônico.
- **[EXPERIMENTAL]** Reautenticação, press-and-hold, confirmação digitada ou segunda etapa podem ser avaliados, sempre com alternativa acessível.
- **[RESEARCH HYPOTHESIS]** Exibir variação em relação ao preço pedido pode reduzir erro de ordem de grandeza; deve ser testado antes de se tornar requisito.

## 7. Acessibilidade

Declarações de acessibilidade devem citar padrão, versão, nível e método de avaliação. Referências consultadas em 2026-08-20:

- [WCAG 2.2 — 2.5.8 Target Size (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html): 24 × 24 CSS px ou alternativa de espaçamento, sujeito às exceções do critério.
- [WCAG 2.2 — 2.5.5 Target Size (Enhanced)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html): 44 × 44 CSS px, sujeito às exceções do critério.
- [Material accessibility](https://m3.material.io/foundations/accessible-design/accessibility-basics): referência de plataforma para Android.
- [Apple Human Interface Guidelines — Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility): referência de plataforma Apple.

- **[REQUIRED]** Controles devem atender ao critério aplicável da plataforma declarada.
- **[RECOMMENDED]** Ações primárias em campo devem usar targets ampliados e ser validadas sob mobilidade, brilho externo e tecnologia assistiva.

O perfil não atribui números de plataforma à Lei de Fitts nem transforma pesquisas de memória de trabalho em limite fixo de componentes por tela.

## 8. Recomendações e scores

- **[REQUIRED]** Inferência não pode ser apresentada como fato declarado.
- **[REQUIRED]** Recomendação deve indicar origem, versão e razões disponíveis.
- **[RECOMMENDED]** Exibir proveniência e data de confirmação em linguagem compreensível, sem expor detalhes internos desnecessários.
- **[RESEARCH HYPOTHESIS]** Intervalos, comparáveis e fatores de ponderação podem melhorar calibração de confiança; validar com usuários.

## 9. Declaração de cobertura

Implementações devem listar capacidades suportadas, experimentais, ausentes e gaps conhecidos. “Compatibilidade total”, “paridade completa” e certificação não podem ser inferidas deste draft.

## 10. Não objetivos

- impor layout, tecnologia, número de etapas ou duração;
- definir estados futuros de `Offer`;
- conceder acesso por presença em tela ou relação operacional;
- estabelecer requisito jurídico ou de biometria universal;
- prescrever coleta de telemetria ou classificação emocional.
