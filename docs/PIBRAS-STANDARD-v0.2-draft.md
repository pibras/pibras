# PIBRAS Standard v0.2 Draft

## Padrão aberto, governança e plano de implementação para dados imobiliários no Brasil

**Versão:** v0.2  
**Status:** draft de reconciliação / RFC  
**Data:** 19 de junho de 2026  
**Base:** revisão do documento `PIBRAS_conceitos_completos.md`, incorporando feedback estratégico, lacunas técnicas e considerações de implementação.

> Este documento ainda não substitui a baseline técnica v0.1.0. Ele define o alvo de reconciliação descrito em `mappings/v0.1.0-code-to-v0.2.md`.

---

# 1. Resumo executivo

O PIBRAS, Portfólio Imobiliário do Brasil, deve nascer como um **padrão aberto de dados imobiliários**, não como mais um CRM, ERP, site, portal ou stack fechada.

A tese central permanece:

**PIBRAS é o padrão. A stack é apenas uma forma de implementar.**

O documento original consolidou uma visão forte: separar `Property` de `Listing`, tratar importação e migração como porta de entrada, preparar dados para inteligência artificial e permitir que CRMs, portais, sites, sistemas legados e ferramentas internas conversem por meio de uma linguagem comum.

Esta versão ajusta a proposta para torná-la mais crível, adotável e tecnicamente sustentável. As principais correções são:

- Esta versão também reconcilia a visão v0.2 com os artefatos técnicos já existentes no projeto: `schema/mbras.schema.json`, `db/schema.sql`, `types/mbras.ts`, `README.md` e `docs/PIBRAS-STANDARD-v0.1.md`.
- PIBRAS precisa de **governança aberta real**, não apenas da afirmação de que é aberto.
- O padrão deve se apoiar em **prior art** internacional e nacional, como RESO, OpenImmo, schema.org e feeds de portais brasileiros.
- `mb_code` não deve ser campo canônico do padrão. Deve virar um `external_id` namespaced.
- A decisão já implementada de `Money` como `{ amount, currency }`, com `amount` em centavos, deve ser preservada. Campos como `asking_price_brl` e `minimum_price_brl` não devem ser a convenção canônica.
- A decisão já implementada de `Building -> Unit -> Property` deve ser preservada: `Unit` é a âncora durável de identidade física e deduplicação; `Property` é o engajamento/inventário comercial.
- A modelagem precisa incluir desde o início `Organization`, `Tenant`, `Geography`, `Deal` e uma camada clara de identidade e posse de dados.
- LGPD precisa ser desenhada como arquitetura, não como checklist.
- Os mecanismos de segurança precisam ser unificados em um modelo consistente de autorização.
- `ExposurePolicy` precisa ter schema e semântica de decisão, com default-deny, precedência de regras e retorno auditável.
- O padrão precisa de suíte de conformidade com testes golden, não apenas schemas.
- Kafka, Temporal, CQRS e motores de busca externos devem ser estágios futuros, não dependências do MVP.
- Geração de feeds para ZAP, VivaReal, OLX e outros portais deve ser saída de primeira classe.
- O PIBRAS Match deve começar com regras auditáveis antes de evoluir para aprendizado de máquina.
- O projeto precisa de um modelo de sustentabilidade: padrão aberto, serviços pagos opcionais, conectores, nuvem gerenciada e suporte.

---

# 2. Posicionamento

## 2.1 O que é o PIBRAS

PIBRAS é uma iniciativa para criar uma camada comum de organização, importação, validação, normalização, distribuição e governança de dados imobiliários no Brasil.

Ele conecta:

- imobiliárias;
- incorporadoras;
- CRMs;
- ERPs;
- portais imobiliários;
- sites próprios;
- fornecedores de tecnologia;
- planilhas;
- XMLs;
- APIs;
- ferramentas de BI;
- ferramentas de IA;
- desenvolvedores e parceiros do setor.

## 2.2 O que o PIBRAS não é

PIBRAS não deve ser posicionado como:

- o novo CRM da MBRAS;
- substituto obrigatório de Kenlo, Vista, Jetimob, Imobzi ou qualquer fornecedor;
- clone brasileiro de MLS americano;
- dependência obrigatória de TwentyCRM, Directus, Windmill, Hermes Agent ou Metabase;
- produto fechado de uma única empresa;
- motor de IA antes de ser um padrão de dados confiável.

## 2.3 Frase central

**PIBRAS é uma infraestrutura aberta para organizar, migrar, integrar e distribuir dados imobiliários no Brasil.**

## 2.4 Frase institucional revisada

**O PIBRAS, Portfólio Imobiliário do Brasil, é uma iniciativa aberta para criar um padrão nacional de dados imobiliários, conectando sistemas, portais, CRMs, incorporadoras, imobiliárias e desenvolvedores em torno de uma linguagem comum, com governança, segurança e interoperabilidade desde a origem.**

## 2.5 Identidade institucional a decidir

Antes de qualquer lançamento público, é necessário decidir quem assina a iniciativa inicial:

- MBRAS como idealizadora e primeira usuária;
- IBVI como patrocinadora técnica, caso a camada de valuation, AVM, liquidez e inteligência comercial venha dela;
- uma entidade neutra ou grupo de trabalho, caso a ambição seja adoção por concorrentes e fornecedores externos.

O ponto crítico: se o PIBRAS parecer controlado por uma única brokerage, fornecedores e concorrentes terão menos incentivo para adotar. A melhor narrativa é:

**PIBRAS nasce de uma necessidade real de mercado, com um primeiro patrocinador, mas deve operar sob governança aberta e neutra.**

Recomendação objetiva: criar a organização pública do padrão sob uma identidade neutra, com MBRAS/IBVI como patrocinadores iniciais e primeiros casos de uso, não como donos fechados do vocabulário. A neutralidade deve aparecer no GitHub, no processo de RFC, na licença e na composição mínima do Working Group.

---

# 3. Governança aberta

Para que o PIBRAS seja realmente aberto, a abertura precisa estar no processo, na licença e no modelo de decisão.

## 3.1 Estrutura recomendada

Criar um **PIBRAS Working Group** com:

- mantenedores técnicos;
- representantes de imobiliárias;
- representantes de incorporadoras;
- fornecedores de CRM e ERP;
- fornecedores de portais e mídia;
- especialistas em LGPD;
- desenvolvedores independentes;
- parceiros de dados e inteligência.

Esse grupo não precisa nascer grande. Pode começar com poucos mantenedores, mas o modelo deve ser público desde o início.

## 3.2 Processo de evolução

O padrão deve evoluir por RFCs:

```txt
1. Proposta de mudança
2. Discussão pública
3. Revisão técnica
4. Compatibilidade com versões anteriores
5. Decisão dos mantenedores
6. Publicação em versão nova
```

Cada mudança relevante deve explicar:

- problema que resolve;
- impacto em implementações existentes;
- campos adicionados, removidos ou alterados;
- migração recomendada;
- exemplos de payload;
- impacto em privacidade e segurança.

## 3.3 Licenças propostas

Modelo inicial recomendado:

- **Apache-2.0** para código, schemas, SDKs e implementações de referência.
- **CC BY 4.0** para documentação, especificação textual e guias.

A decisão exata deve ser validada juridicamente, mas a direção é importante: permitir adoção comercial ampla sem transformar o padrão em propriedade operacional de um único fornecedor.

## 3.4 Compatibilidade e certificação

No futuro, o PIBRAS pode criar selos como:

```txt
PIBRAS Compatible
PIBRAS Import Ready
PIBRAS Portal Feed Ready
PIBRAS Secure Exposure Ready
```

No MVP, isso não precisa virar certificação formal. Basta uma checklist pública de compatibilidade.

---

# 4. Relação com padrões existentes

PIBRAS não deve reinventar tudo do zero. Ele deve funcionar como um **perfil brasileiro de interoperabilidade imobiliária**, com mapeamentos claros para padrões e formatos existentes.

## 4.1 RESO

RESO Data Dictionary é a principal referência internacional para padronização de dados imobiliários, especialmente em mercados com MLS.

PIBRAS deve:

- mapear entidades e campos relevantes para RESO;
- aproveitar nomenclaturas e conceitos maduros quando fizer sentido;
- documentar divergências brasileiras;
- evitar copiar mecanicamente um modelo pensado para outro mercado.

Posicionamento recomendado:

**PIBRAS é inspirado por RESO, adaptado ao Brasil, com LGPD, portais brasileiros, dados off-market e operação de alto padrão como requisitos nativos.**

Escopo MVP do mapeamento RESO:

```txt
Entram no MVP:
- Property
- Unit
- Building/Condominium quando houver equivalência útil
- MediaAsset
- Listing/PublicationChannel como perfil PIBRAS, não como cópia direta
- enums de tipo, status e transação

Ficam fora do MVP:
- contatos, proprietários e dados pessoais;
- MLS-specific fields sem equivalente brasileiro;
- campos financeiros sem necessidade imediata;
- enumerações que conflitam com portais brasileiros ou operação off-market.
```

Decisão recomendada sobre enums: usar enums próprios do PIBRAS quando o mercado brasileiro exigir diferença clara, mas documentar o mapeamento para RESO. Não importar cegamente listas extensas do RESO apenas para parecer compatível.

## 4.2 OpenImmo

OpenImmo é uma referência europeia para intercâmbio de dados imobiliários, historicamente muito associada a XML.

PIBRAS deve observar OpenImmo para:

- transporte de dados entre sistemas;
- estrutura de imóveis, marketing e geografia;
- extensibilidade;
- compatibilidade com fluxos de importação e exportação.

## 4.3 schema.org

schema.org `RealEstateListing` deve ser tratado como alvo para publicação web e SEO, não como modelo canônico completo.

PIBRAS deve gerar dados estruturados compatíveis para:

- páginas públicas de imóveis;
- páginas de empreendimentos;
- experiências de busca;
- indexação por buscadores.

## 4.4 Feeds de portais brasileiros

ZAP, VivaReal, OLX, Chaves na Mão, Imovelweb e portais regionais devem ser tratados como **canais de distribuição**.

PIBRAS não deve usar o XML de um portal como modelo canônico. O fluxo correto é:

```txt
Modelo canônico PIBRAS
↓
Policy de exposição
↓
Transformação por canal
↓
Feed válido para portal
```

Essa geração de feed deve ser uma entrega de primeira classe, porque é uma dor concreta do mercado e um gancho forte de adoção.

---

# 5. Modelo de dados canônico

## 5.0 Alinhamento com os artefatos técnicos existentes

O repositório já contém uma v0.1.0 técnica em:

```txt
schema/mbras.schema.json
db/schema.sql
types/mbras.ts
README.md
```

Esses artefatos não devem ser descartados. Em dois pontos, eles tomaram decisões melhores do que o documento fundador e melhores do que a primeira redação da v0.2:

```txt
1. Money = { amount, currency }, com amount em centavos.
2. Building -> Unit -> Property, com Unit como identidade física durável.
```

Esta v0.2 deve ser lida como uma reconciliação:

| Tema | v0.1 fundador | v0.1.0 técnica atual | Decisão v0.2 alinhada |
|---|---|---|---|
| Código de imóvel | `mb_code` como campo relevante | `property.code` como código MBRAS | UUID canônico + `external_ids[]`; código MBRAS vira external id namespaced em v0.2 |
| Dinheiro | campos `_brl` em reais inteiros | `Money { amount, currency }`, amount em centavos | manter `Money { amount, currency }`; abandonar `_brl` como convenção canônica |
| Identidade física | Property como centro narrativo | `Building -> Unit -> Property`, matrícula em `Unit` | manter `Unit` como âncora de deduplicação e identidade física |
| Bairro/geografia | strings normalizadas | `neighborhood` com aliases, centroid e polígonos | evoluir `Neighborhood` para `Geography`, mantendo aliases e geodados |
| Proprietário | `Owner` plano | `owner` + `property_owners` | evoluir para `Party` + `Ownership`; não quebrar o schema atual sem migração |
| Segurança | `ExposureRule` com flags | `exposure_level` + `field_visibility` | evoluir para `ExposurePolicy` com semântica default-deny e schema explícito |
| Ingestão | `ImportSource/ImportBatch/ImportMapping` | `ingestion_record` + `pending_change` | manter registro bruto e mudanças pendentes; renomear ou mapear sem perder semântica |
| Conformidade | documentação em prosa | validação JSON Schema/Zod/SQL | **entregue:** corpus golden em `tests/golden/` + runner `scripts/validate_conformance.py` |

O arquivo de reconciliação **já foi publicado** dentro do projeto atual:

```txt
mappings/v0.1.0-code-to-v0.2.md
```

Ele diz, campo por campo, o que permanece, o que é renomeado, o que vira extensão e o que exige migração. As entidades-alvo desta reconciliação (`external_ids[]`, `Organization`, `Tenant`, `Party`, `Ownership`, `Geography`, `ExposurePolicy`, `DataSubjectRequest`) **já estão implementadas** em `schema/mbras.schema.json`, `types/mbras.ts` e `db/schema.sql`, e o corpus de conformidade em `tests/golden/` é verificado pelo runner `scripts/validate_conformance.py`. Portanto a v0.2 não é mais um alvo puramente futuro: a baseline técnica já a antecipa, e a promoção a padrão estável depende do rito de RFC (ver `VERSIONING.md` e `RFC_PROCESS.md`), não de reimplementação.

## 5.1 Princípio

Cada sistema externo pode chamar o mesmo conceito por nomes diferentes:

```txt
valor
preco_venda
preço
listingPrice
sale_value
```

Dentro do PIBRAS, o campo precisa ter um nome canônico.

Exemplo:

```json
{
  "asking_price": {
    "amount": 1750000000,
    "currency": "BRL"
  }
}
```

`amount` deve representar a menor unidade monetária da moeda, como centavos para BRL. Isso evita perda de precisão em condomínio, IPTU, aluguel, comissão, taxas e operações internacionais.

Campos com moeda no nome, como `asking_price_brl`, podem existir em exportadores específicos, mas não devem ser a convenção canônica do padrão.

## 5.2 Identificadores

O identificador canônico deve ser um UUID interno do PIBRAS.

Códigos próprios de empresas devem entrar em `external_ids`.

Exemplo:

```json
{
  "id": "018f4dd8-8f76-7af2-b503-8d805c58d111",
  "external_ids": [
    {
      "namespace": "mbras",
      "key": "property_code",
      "value": "MB18495"
    },
    {
      "namespace": "kenlo",
      "key": "property_id",
      "value": "123456"
    }
  ]
}
```

Isso evita transformar uma convenção de uma empresa em regra do padrão aberto.

## 5.3 Entidades essenciais

O MVP revisado deve incluir:

```txt
Organization
Tenant
User
Broker
Building
Unit
Property
Listing
Geography
Party
Ownership
MediaAsset
Document
ExposurePolicy
PublicationChannel
ImportSource
ImportBatch
ImportMapping
AuditEvent
```

Entidades para fases seguintes:

```txt
Lead
ClientProfile
LeadInterest
Visit
Offer
Deal
Transaction
ComparableProperty
PropertyValuation
PropertyIntelligence
MatchRecommendation
FeedbackSignal
```

## 5.4 Organization e Tenant

`Organization` representa a empresa ou grupo que participa do ecossistema.

`Tenant` representa o limite operacional e de isolamento de dados.

Essas entidades são obrigatórias em qualquer implementação compartilhada, porque respondem perguntas fundamentais:

- quem é dono do dado?
- quem pode ver?
- quem pode publicar?
- quem pode importar?
- quem pode exportar?
- qual base está isolada de qual base?
- qual política de retenção se aplica?

## 5.5 Geography

Bairro, cidade, zona, região e microrregião não devem ser apenas strings soltas.

O schema técnico atual usa `Neighborhood`. A v0.2 deve evoluir isso para `Geography`, sem perder as boas decisões já implementadas: aliases, cidade, UF, zona, centroid, polígono e indicadores de mercado.

PIBRAS deve ter `Geography` para:

- normalizar bairros;
- resolver abreviações;
- mapear aliases;
- apoiar deduplicação;
- permitir busca por região;
- permitir inteligência de mercado.

Exemplo:

```txt
Jd. Europa -> Jardim Europa
V. Nova Conceição -> Vila Nova Conceição
Itaim -> Itaim Bibi ou Itaim Paulista, conforme cidade e contexto
```

## 5.6 Party, Owner e Ownership

Em vez de modelar apenas `Owner`, o padrão deve usar `Party` para pessoas e organizações.

`Party` pode exercer papéis diferentes:

- proprietário;
- comprador;
- locatário;
- incorporadora;
- construtora;
- corretor parceiro;
- representante legal.

`Ownership` liga uma `Party` a uma `Unit` ou a um `Property`, com percentual, tipo de posse e regras de acesso.

Essa estrutura é mais compatível com LGPD, multi-propriedade e operações empresariais.

Compatibilidade com o schema atual:

```txt
owner -> Party com role owner
property_owners -> Ownership
owner_type -> party_type
tax_id -> identificador fiscal sensível em Party
```

A transição deve ser feita por migração explícita, não por substituição silenciosa.

---

# 6. Property e Listing

A separação entre `Property` e `Listing` continua sendo a decisão mais importante da arquitetura.

A v0.2 acrescenta uma segunda separação igualmente importante, já presente no schema técnico:

```txt
Unit != Property
Property != Listing
```

Sem isso, deduplicação e histórico comercial ficam misturados.

## 6.1 Property

`Property` é o registro de inventário ou engajamento comercial de uma unidade.

Contém:

- `unit_id`;
- tipo de transação;
- status operacional;
- preços;
- histórico;
- origem;
- governança;
- brokers;
- proprietários;
- inteligência comercial;
- vínculo com listing e canais.

O mesmo `Unit` pode gerar mais de um `Property` ao longo do tempo: venda em 2024, locação em 2025, revenda em 2027, off-market em outro momento.

## 6.2 Listing

`Listing` é a exposição comercial de um `Property` em um canal.

Um mesmo imóvel pode ter:

- listing público no site;
- listing privado para brokers;
- listing off-market;
- listing para portais;
- listing internacional;
- listing para PDF;
- listing para campanha;
- listing com preço sob consulta;
- listing sem fachada;
- listing apenas por bairro.

## 6.3 Regra

```txt
Unit guarda a identidade física durável.
Property guarda o engajamento comercial e o inventário.
Listing guarda a narrativa e a exposição por canal.
ExposurePolicy decide o que pode aparecer.
```

## 6.4 Unit como âncora de deduplicação

`Unit` representa a identidade física durável:

- matrícula;
- prédio;
- número da unidade;
- andar;
- torre;
- endereço físico;
- áreas;
- tipologia;
- atributos físicos estáveis.

Deduplicação deve acontecer primeiro em `Unit`, não em `Property`.

Exemplo:

```txt
Building: Edifício X
Unit: unidade 2101, matrícula Y, 570 m², 4 suítes
Property 1: venda captada em 2024
Property 2: off-market em 2026
Listing 1: site público
Listing 2: PDF privado
Listing 3: portal com endereço mascarado
```

Essa decisão evita que o mesmo imóvel físico seja recriado a cada novo ciclo comercial.

---

# 7. Privacidade, LGPD e autorização

LGPD não pode ser item de checklist. Precisa ser arquitetura.

## 7.1 Dados sensíveis e de alto risco

Campos de maior cuidado:

- nome do proprietário;
- CPF/CNPJ;
- telefone;
- e-mail;
- endereço completo;
- número da unidade;
- matrícula;
- documentos;
- preço mínimo aceito;
- motivo de venda;
- situação financeira;
- observações internas;
- histórico de negociação.

Esta lista é normativa e **legível por máquina**: cada campo é marcado no `schema/mbras.schema.json` com `x-pii: true` e `x-sensitivity` (ex.: `Owner.tax_id`, `Party.tax_id`, `Property.min_accepted_price`). Geradores de projeção e de feed devem derivar os campos sensíveis dessas anotações, não de uma lista paralela em prosa. A cobertura de `x-pii` deve ser expandida até cobrir todos os itens acima.

## 7.2 Bases de desenho

Toda implementação PIBRAS deve prever:

- base legal para tratamento;
- finalidade do tratamento;
- minimização de dados;
- política de retenção;
- trilha de auditoria;
- controle de acesso por finalidade;
- consentimento quando aplicável;
- atendimento a direitos do titular;
- pseudonimização ou anonimização em camadas de leitura;
- logs de acesso a campos sensíveis;
- segregação por tenant;
- criptografia em repouso e em trânsito.

Além disso, a implementação multi-tenant precisa modelar a relação controlador/operador:

```txt
Tenant controlador: decide finalidade e base legal dos dados.
Operador: processa em nome do controlador.
Suboperador: serviço contratado para storage, IA, enriquecimento, assinatura ou comunicação.
```

Quando uma imobiliária importa sua base para uma infraestrutura PIBRAS gerenciada por outra organização, o contrato e o sistema precisam saber:

- quem é controlador;
- quem é operador;
- quais suboperadores existem;
- para quais finalidades cada campo pode ser tratado;
- por quanto tempo cada dado pode ser retido;
- se há transferência internacional;
- como atender requisições do titular.

Campos recomendados para v0.2:

```txt
legal_basis
processing_purpose
retention_policy_id
data_controller_tenant_id
data_processor_org_id
international_transfer_allowed
data_subject_request_ids
```

Também deve existir uma entidade ou endpoint para DSAR:

```txt
DataSubjectRequest
- id
- tenant_id
- party_id
- request_type: access | correction | deletion | portability | objection
- status
- due_at
- fulfilled_at
- audit_log_ref
```

## 7.3 Modelo único de autorização

O documento original continha mecanismos sobrepostos:

- `confidentiality_level`;
- `Listing.visibility`;
- `ExposureRule`;
- field-level security.

Isso pode gerar conflito.

Esta versão propõe unificar tudo em `ExposurePolicy`, baseada em RBAC e ABAC.

## 7.4 ExposurePolicy

`ExposurePolicy` decide se um sujeito pode executar uma ação sobre um recurso, campo ou canal.

Dimensões:

```txt
subject: usuário, broker, diretor, sistema, portal, cliente qualificado
resource: property, listing, media, document, owner, price, address
action: read, write, publish, export, send, approve
context: tenant, canal, finalidade, status, relacionamento comercial
field: address.number, owner.phone, min_accepted_price
channel: website, portal, whatsapp, crm, pdf, internal_app
```

Semântica obrigatória:

```txt
1. Default deny para qualquer campo sensível, ação de escrita, exportação ou publicação.
2. Default allow apenas para campos explicitamente públicos de listings publicados.
3. Regra específica do recurso vence regra default do nível de exposição.
4. Deny explícito vence allow.
5. Se duas regras permitem escopos diferentes, vence a mais restritiva.
6. Se a regra exige aprovação e ela não existe, a decisão é needs_approval, não allow.
7. Toda decisão deve retornar reason_code auditável.
8. Toda leitura de campo sensível deve poder gerar log.
```

Modelo de avaliação:

```txt
input:
  subject roles, tenant, broker assignment, client qualification
  resource type, resource id, exposure level, record state
  action, field, channel, purpose

evaluation:
  load global defaults
  load tenant policy
  load property/unit/listing policy
  load channel policy
  apply deny rules
  apply approval requirements
  apply field-level allow rules
  return decision

output:
  allow | deny | mask | needs_approval
  reason_code
  applied_rule_ids
  masked_fields
```

Schema mínimo:

```json
{
  "id": "uuid",
  "tenant_id": "uuid",
  "resource_type": "property",
  "resource_id": "uuid",
  "exposure_level": "confidential",
  "rules": [
    {
      "effect": "allow",
      "actions": ["read"],
      "fields": ["address.street"],
      "roles": ["broker"],
      "conditions": {
        "broker_is_assigned": true
      }
    },
    {
      "effect": "deny",
      "actions": ["read", "export"],
      "fields": ["address.number", "owner.tax_id"]
    }
  ],
  "requires_approval_for": ["export", "send_pdf"],
  "allowed_channels": ["crm", "off_market_pdf"],
  "audit_sensitive_reads": true
}
```

Exemplo de decisão:

```txt
Diretor pode ler owner.name e min_accepted_price.
Broker responsável pode ler address.street, mas não address.number.
Portal público pode receber bairro, fotos aprovadas e preço público.
Cliente qualificado pode receber PDF privado após aprovação.
```

## 7.5 Camada de leitura segura

A API não deve apenas esconder campos no frontend. Ela deve aplicar políticas no backend.

O mesmo endpoint pode responder diferente conforme o usuário:

```txt
Público:
- bairro
- tipo
- metragem
- preço: sob consulta
- endereço completo: null

Broker autorizado:
- rua
- bairro
- preço público
- mídia privada aprovada
- número: null

Diretoria:
- endereço completo
- proprietário
- preço mínimo
- documentos sensíveis
```

---

# 8. Importação, migração e entity resolution

## 8.1 Import-first

A principal porta de entrada do PIBRAS deve ser migração.

O mercado já tem dados espalhados em:

- planilhas;
- CRMs;
- ERPs;
- XMLs de portais;
- bancos legados;
- sites antigos;
- sistemas próprios;
- exportações manuais.

Por isso, o primeiro produto não deve ser IA. Deve ser confiança na importação.

## 8.2 Fluxo recomendado

```txt
1. Criar ImportSource
2. Receber CSV, Excel, XML, API ou dump
3. Fazer profiling da fonte
4. Sugerir mapeamento para o modelo PIBRAS
5. Permitir ajuste humano do mapeamento
6. Normalizar valores
7. Validar campos obrigatórios
8. Detectar duplicatas primeiro em Unit
9. Aplicar regras de survivorship
10. Enviar itens duvidosos para revisão humana
11. Fazer upsert no modelo canônico
12. Registrar AuditEvent
13. Gerar relatório de qualidade
```

## 8.3 Deduplicação

Deduplicação é uma das partes mais difíceis do PIBRAS.

Ela deve ser tratada como subsistema, não como detalhe.

A deduplicação canônica deve operar nesta ordem:

```txt
1. Building
2. Unit
3. Property
4. Listing
```

`Unit` é a âncora: matrícula, endereço físico, prédio, unidade, área, andar, coordenadas e atributos físicos estáveis. `Property` pode mudar conforme ciclo comercial; `Listing` muda conforme canal.

Componentes:

- normalização de endereço;
- geocoding;
- aliases de bairro;
- blocking strategy;
- fuzzy match;
- comparação de atributos;
- comparação semântica de descrições;
- comparação de mídia quando viável;
- score de confiança;
- revisão humana;
- logs de decisão.

Critérios mínimos de aceite para o MVP:

```txt
auto_merge_threshold: >= 0.95
manual_review_band: 0.75 até 0.95
auto_reject_threshold: < 0.75
false_merge_tolerance: menor que false_duplicate_tolerance
```

Em outras palavras: é melhor mandar um possível duplicado para revisão do que mesclar duas unidades físicas diferentes. Merge errado é mais caro do que duplicata temporária.

Cada candidato de dedupe deve registrar:

```txt
candidate_a
candidate_b
entity_level: building | unit | property | listing
score
matched_features
missing_features
decision: auto_merge | review | reject
reviewer_id
reason
```

Fonte canônica de endereço para o MVP:

```txt
1. CEP e UF/cidade normalizados por base nacional disponível.
2. Neighborhood/Geography interno com aliases.
3. Geocoding externo apenas como enriquecimento, não como fonte única de verdade.
4. Endereço original preservado em neighborhood_raw/raw_payload_ref para auditoria.
```

## 8.4 Survivorship

Quando duas fontes divergem, o padrão precisa definir qual campo vence.

Tabela de survivorship por campo:

| Campo | Quem vence | Fonte externa de menor confiança em conflito |
|---|---|---|
| Endereço completo | fonte interna aprovada | vira `pending_change` |
| Status comercial | decisão manual mais recente | vira `pending_change` |
| Preço público | listing aprovado por canal | vira `pending_change` |
| Preço mínimo aceito (PII) | dado proprietário interno | nunca sobrescrito; vira `pending_change` |
| Fotos | mídias aprovadas (não upload bruto) | anexadas como sugestão |
| Descrição | texto aprovado para o canal | vira `pending_change` |
| Dados de proprietário / `tax_id` (PII) | dado proprietário interno | nunca sobrescrito automaticamente; exige revisão |

Thresholds de deduplicação (entity resolution): `score >= 0.95` → `auto_merge`; `0.75 <= score < 0.95` → `needs_review`; `score < 0.75` → tratado como não-duplicado.

Fixtures de conformidade que exercitam estas regras: `tests/golden/pending-change.external-overwrite.json` (preço de menor confiança vira revisão), `tests/golden/pending-change.owner-pii-protected.json` (PII de proprietário nunca sobrescrita por fonte externa), `tests/golden/unit.duplicate-candidate.json` (auto_merge acima do limite) e `tests/golden/unit.dedupe-review-band.json` (banda 0,75–0,95 exige revisão).

Regra de ouro:

**Dados externos entram como sugestão, conflito, enriquecimento ou nova versão. Nunca destroem dado proprietário sensível sem governança.**

## 8.5 Off-market

Deduplicar unidades off-market é mais difícil, porque endereço, fachada e proprietário podem estar ocultos.

O PIBRAS deve prever:

- campos de matching internos não expostos;
- hash ou fingerprint de endereço;
- comparação por condomínio, unidade, área, andar e atributos;
- revisão humana obrigatória em casos de baixa confiança;
- logs para justificar merges.

Regra específica: em off-market, a existência de dados ocultos para publicação não significa ausência de dados para dedupe. O sistema pode manter fingerprint interno de endereço/unidade, desde que protegido por `ExposurePolicy`, logs e finalidade legal.

---

# 9. Distribuição e feeds

## 9.1 Distribution Layer

Depois que os dados estão normalizados, o PIBRAS deve distribuir para:

- site próprio;
- CRM;
- portais;
- PDFs;
- campanhas;
- apps internos;
- dashboards;
- parceiros;
- ferramentas de IA.

## 9.2 Feed generation como produto central

Geração de feed para portais deve ser tratada como produto central do MVP.

Isso significa:

- mapear campos canônicos para cada portal;
- aplicar `ExposurePolicy` antes da exportação;
- validar XML ou payload antes do envio;
- registrar o que foi enviado;
- registrar erros de publicação;
- permitir preview do feed por canal;
- evitar vazar preço, endereço, fachada ou proprietário por erro de mapeamento.

Fluxo:

```txt
Property + Listing + MediaAsset + ExposurePolicy
↓
PortalFeedMapper
↓
PortalFeedValidator
↓
PublicationLog
↓
Portal
```

## 9.3 Canais

`PublicationChannel` deve representar:

- site próprio;
- portal;
- CRM;
- WhatsApp;
- PDF;
- campanha;
- app interno;
- integração customizada.

Cada canal tem sua própria política de dados, formato e auditoria.

---

# 10. PIBRAS Match e Intelligence

## 10.1 Começar simples

O PIBRAS Match não deve começar como IA complexa.

Versão 1:

- regras explícitas;
- pesos configuráveis;
- razões de recomendação;
- filtros rígidos de orçamento, localização e status;
- explicação legível para o broker;
- feedback manual.

Versão 2:

- aprendizado com visitas;
- propostas;
- recusas;
- tempo até contato;
- conversão por broker;
- imóveis salvos;
- objeções registradas.

Versão 3:

- learning-to-rank;
- embeddings;
- personalização por perfil;
- reativação preditiva;
- otimização por timing comercial.

## 10.2 Guardrails

O match aspiracional precisa de limite.

Não basta mostrar imóveis acima do orçamento com a justificativa de encantamento.

Regras mínimas:

- faixa máxima acima do orçamento;
- motivo explícito da recomendação;
- confiança do match;
- alerta quando houver risco de desalinhamento;
- possibilidade de o broker rejeitar e explicar;
- nenhuma mensagem automática ao cliente sem aprovação humana.

## 10.3 Feedback signal

O motor de recomendação só aprende se houver sinal.

Eventos úteis:

```txt
property_recommended
broker_accepted_recommendation
broker_rejected_recommendation
client_viewed
client_saved
visit_scheduled
visit_completed
offer_made
offer_lost
deal_closed
objection_recorded
```

## 10.4 IBVI como diferencial opcional

Se IBVI tiver modelos de valuation, liquidez, AVM, potencial de valorização ou inteligência de mercado, isso deve entrar como camada opcional.

Separação recomendada:

```txt
PIBRAS Standard: aberto e neutro
PIBRAS Core: implementação de referência
IBVI Intelligence: camada proprietária opcional de dados, valuation e scoring
```

Essa separação protege a abertura do padrão e preserva um diferencial comercial.

---

# 11. Arquitetura de referência

## 11.1 Princípio

Começar com a menor arquitetura que prove o padrão.

Evitar dependências prematuras como Kafka, Temporal, CQRS completo e Elasticsearch no MVP.

## 11.2 Estágio 1: MVP

Stack suficiente:

```txt
Postgres
API REST com OpenAPI
JSON Schema
Worker simples para importação
Storage de mídia
Interface administrativa simples
Exportador de feed
Metabase ou dashboards básicos
```

Postgres pode cobrir muito:

- dados relacionais;
- auditoria;
- full-text search;
- `pg_trgm` para fuzzy search;
- `pgvector` para embeddings, quando necessário;
- PostGIS para geografia, se adotado;
- jobs simples com fila leve ou tabela de tarefas.

## 11.3 Estágio 2: Operação real

Adicionar:

- fila de jobs;
- workers separados;
- motor de busca como Typesense, Meilisearch, OpenSearch ou Elasticsearch;
- cache;
- webhooks;
- observabilidade;
- connector framework;
- ambiente de homologação.

## 11.4 Estágio 3: Escala e integrações críticas

Adicionar apenas quando houver volume e criticidade:

- Kafka ou Pub/Sub;
- Temporal;
- CQRS mais formal;
- event sourcing parcial;
- pipelines de ML;
- conectores bidirecionais robustos;
- certificação de compatibilidade.

## 11.5 Stack recomendada, não obrigatória

A stack de referência pode continuar sendo:

```txt
PIBRAS Core
Postgres
Directus
Windmill
TwentyCRM
Hermes Agent
Metabase
```

Mas a mensagem externa deve ser:

**Quem adota o PIBRAS adota o padrão. A stack é uma opção de implementação.**

---

# 12. Modelo open-core e sustentabilidade

Padrões abertos morrem quando não há manutenção.

PIBRAS precisa separar o que é aberto do que sustenta o projeto.

## 12.1 Aberto

Deve ser aberto:

- especificação;
- JSON Schemas;
- OpenAPI básica;
- exemplos de payload;
- guias de mapeamento;
- modelo de governança;
- SDKs básicos;
- validador local;
- exemplos de importação;
- documentação pública.

## 12.2 Comercial opcional

Pode ser pago:

- cloud gerenciada;
- conectores mantidos com SLAs;
- Migration Studio visual;
- suporte enterprise;
- implantação assistida;
- auditoria de dados;
- feeds avançados para portais;
- homologação de conectores;
- PIBRAS Match;
- IBVI Intelligence;
- modelos de valuation, liquidez e mercado;
- consultoria de LGPD e governança.

## 12.3 Regra

O padrão aberto não pode depender do produto pago para existir.

O produto pago deve facilitar adoção, operação e suporte.

---

# 13. Repositórios sugeridos

Estrutura inicial:

```txt
pibras-standard
Especificação, schemas, exemplos, versionamento e RFCs.

pibras-reference-api
Implementação mínima de referência com API e validação.

pibras-connectors
Conectores oficiais e comunitários.

pibras-portal-feeds
Mapeadores e validadores para canais de publicação.

pibras-migration-studio
Interface e fluxos de importação, mapeamento e qualidade.

pibras-sdk-js
SDK TypeScript/JavaScript.

pibras-sdk-python
SDK Python.

pibras-docs
Documentação pública, guias e exemplos.

pibras-match
Motor opcional de recomendação.
```

Para começar, reduzir para:

```txt
pibras-standard
pibras-reference-api
pibras-portal-feeds
```

---

# 14. MVP revisado

## 14.1 Objetivo do MVP

Provar que o PIBRAS consegue:

```txt
Importar dados ruins
↓
Mapear para um modelo canônico
↓
Normalizar
↓
Deduplicar
↓
Aplicar governança e exposição
↓
Distribuir para site, CRM ou portal
```

## 14.2 Entregáveis do MVP

```txt
1. Manifesto e posicionamento
2. Governança e licença inicial
3. De/Para v0.1.0-code -> v0.2
4. Convenção canônica de Money em centavos + currency
5. Unit como âncora formal de deduplicação
6. JSON Schema das entidades do MVP
7. OpenAPI inicial
8. Mapeamento RESO -> PIBRAS parcial e limitado
9. Mapeamento schema.org -> PIBRAS para páginas públicas
10. Modelo de PortalFeed
11. Importador CSV/Excel/XML simples
12. ImportMapping com revisão humana
13. Deduplicação básica com thresholds e logs de decisão
14. ExposurePolicy v0.1 com schema e semântica default-deny
15. API de units, properties e listings
16. Exportador de feed para um canal inicial
17. Relatório de qualidade de importação
18. Corpus de testes golden de conformidade
19. Documentação pública mínima
```

## 14.3 Entidades do MVP revisado

```txt
Organization
Tenant
User
Building
Unit
Property
Listing
Geography
Party
Ownership
MediaAsset
Document
ExposurePolicy
PublicationChannel
ImportSource
ImportBatch
ImportMapping
AuditEvent
DataSubjectRequest
ConformanceTestCase
```

## 14.4 O que fica fora do MVP

```txt
Kafka
Temporal
CQRS completo
Learning-to-rank
IA generativa automática
Conectores bidirecionais complexos
Certificação formal
Marketplace de parceiros
```

## 14.5 Suíte de conformidade

Sem testes verificáveis por máquina, o PIBRAS vira apenas um documento.

O MVP deve conter:

```txt
tests/golden/
  property.valid.json
  property.invalid-money.json
  unit.duplicate-candidate.json
  listing.public-masked.json
  exposure-policy.default-deny.json
  portal-feed.valid.xml
  import-row.pending-change.json
```

Cada implementação compatível deve conseguir:

- validar JSON Schema;
- validar exemplos positivos;
- rejeitar exemplos negativos;
- aplicar `ExposurePolicy` com o mesmo resultado esperado;
- transformar payload canônico em feed esperado;
- registrar `pending_change` quando fonte externa tenta sobrescrever dado mais confiável.

---

# 15. Roadmap de 90 dias

## 15.1 Primeiros 30 dias

- decidir patrocinador institucional inicial;
- definir licença;
- reconciliar v0.1.0 técnica com v0.2 em `mappings/v0.1.0-code-to-v0.2.md`;
- alinhar README, schema, DDL e tipos com as convenções escolhidas;
- preparar a organização/repositório neutro `pibras-standard`;
- escrever manifesto curto;
- criar processo simples de RFC;
- consolidar entidades do MVP;
- escrever JSON Schemas iniciais;
- criar exemplos reais de payload;
- mapear campos básicos de RESO e schema.org;
- definir `ExposurePolicy` v0.1 com schema, default-deny e testes golden.

## 15.2 Dias 31 a 60

- criar API de referência;
- criar importador CSV/Excel;
- criar importador XML genérico;
- criar `ImportMapping`;
- criar relatório de qualidade;
- criar deduplicação básica;
- criar `AuditEvent`;
- criar exportador de feed para um canal inicial;
- validar com uma base real.

## 15.3 Dias 61 a 90

- conectar primeiro CRM ou site;
- gerar feed validado para portal ou formato equivalente;
- publicar documentação pública;
- criar SDK básico;
- abrir primeiros RFCs externos;
- convidar parceiros técnicos;
- rodar piloto com dados reais;
- documentar casos de conflito, duplicidade e exposição sensível.

---

# 16. Decisões obrigatórias antes do lançamento público

```txt
1. Quem assina a iniciativa inicial: MBRAS, IBVI, ambos ou grupo neutro?
2. Qual licença será usada para spec, docs, schemas e código?
3. Qual será o processo de RFC?
4. O padrão será hospedado em organização neutra no GitHub?
5. Qual será o primeiro formato de portal/feed a suportar?
6. Qual CRM ou sistema será o primeiro conector?
7. Qual será a política mínima de LGPD e retenção?
8. Quais campos são obrigatórios no core?
9. Quais campos entram como extensão?
10. Onde termina o padrão aberto e começa o produto comercial?
```

---

# 17. Texto institucional revisado

O PIBRAS, Portfólio Imobiliário do Brasil, nasce como uma iniciativa aberta para organizar, padronizar e integrar dados imobiliários no Brasil.

O mercado ainda opera com bases fragmentadas, cadastros duplicados, integrações frágeis, migrações difíceis e pouca padronização entre CRMs, ERPs, portais, sites, planilhas e sistemas próprios. Cada plataforma fala sua própria linguagem. O resultado é perda de dados, retrabalho, baixa governança e dificuldade para aplicar inteligência artificial com segurança.

O PIBRAS propõe uma camada comum para esse ecossistema.

Mais do que um software, o PIBRAS é um padrão aberto de dados imobiliários. Ele define como imóveis, anúncios, unidades, empreendimentos, proprietários, mídias, documentos, regras de exposição, status, preços e canais devem ser estruturados, importados, validados, auditados e distribuídos.

A iniciativa parte de um princípio simples: o imóvel físico não é a mesma coisa que o anúncio. Um mesmo ativo pode ter diferentes formas de exposição, diferentes níveis de confidencialidade, diferentes canais de publicação e diferentes narrativas comerciais. Essa separação é essencial para um mercado mais profissional, seguro e interoperável.

O PIBRAS poderá ser usado de diferentes formas. Quem quiser começar do zero poderá adotar uma stack de referência. Quem já utiliza CRM, ERP, portal, site próprio ou sistema imobiliário poderá usar apenas o padrão, a API, os conectores, os schemas ou o Migration Studio. A proposta não é substituir todos os sistemas existentes, mas permitir que eles conversem melhor.

O projeto deve nascer com governança aberta, processo de evolução transparente, mapeamento para padrões existentes e arquitetura compatível com LGPD desde a origem.

O objetivo do PIBRAS é criar uma infraestrutura comum para o portfólio imobiliário brasileiro: importável, auditável, extensível, segura, interoperável e preparada para inteligência artificial.

---

# 18. Manifesto curto revisado

O mercado imobiliário brasileiro precisa de uma linguagem comum.

Imóveis, anúncios, mídias, documentos, proprietários, portais, CRMs e sistemas ainda vivem em bases fragmentadas, com integrações frágeis, migrações difíceis e pouca governança.

O PIBRAS nasce para mudar isso.

Não como mais um sistema fechado, mas como um padrão aberto para organizar, migrar, integrar e distribuir dados imobiliários.

Um imóvel não é apenas um anúncio. Um portfólio não é apenas uma lista. Dados imobiliários exigem contexto, segurança, histórico, autorização por canal, auditoria e inteligência.

O PIBRAS é o Portfólio Imobiliário do Brasil: uma infraestrutura aberta para um mercado mais integrado, profissional e preparado para IA.

---

# 19. Princípios revisados

```txt
1. Aberto por processo, licença e governança
2. Independente de fornecedor
3. Inspirado por padrões existentes, adaptado ao Brasil
4. API-first
5. Import-first
6. Migration-ready
7. Connector-based
8. Portal-feed ready
9. Data-model driven
10. LGPD by design
11. Auditável
12. Multi-tenant
13. Multi-origem
14. Multi-canal
15. Seguro por política de exposição
16. Separação entre Property e Listing
17. Dados externos não sobrescrevem dados proprietários sem governança
18. Humano aprova mudanças sensíveis
19. IA só depois de dados confiáveis
20. O padrão deve ser maior do que a ferramenta
21. O ecossistema deve ser maior do que o primeiro patrocinador
```

---

# 20. Próxima ação recomendada

A etapa de reconciliação dentro do projeto atual **já foi entregue**: README, LICENSE, governança, mappings, schema/tipos/DDL, exemplos, corpus golden e o runner de conformidade existem. A árvore real do repositório é:

```txt
README.md
LICENSE
GOVERNANCE.md
RFC_PROCESS.md
AGENTS.md
schema/
  mbras.schema.json          # JSON Schema 2020-12 com $defs (todas as entidades num único arquivo)
types/
  mbras.ts                   # schemas Zod + tipos TypeScript inferidos
db/
  schema.sql                 # DDL Postgres
examples/
  property.sample.json
mappings/
  v0.1.0-code-to-v0.2.md
  reso-to-pibras.md
  schema-org-to-pibras.md
  portal-feed-notes.md
tests/
  README.md
  golden/
    conformance-cases.json
    property.valid.json
    property.invalid-money.json
    money.centavos.expected.json
    listing.public-masked.json
    exposure-policy.default-deny.json
    data-subject-request.valid.json
    import-row.pending-change.json
    pending-change.external-overwrite.json
    unit.duplicate-candidate.json
    portal-feed.valid.xml
scripts/
  validate_conformance.py    # runner: JSON Schema + avaliação de ExposurePolicy + feed + índice de casos
docs/
  PIBRAS-STANDARD-v0.1.md
  MBRAS-PROPERTY-STANDARD.md
  PIBRAS-STANDARD-v0.2-draft.md
  VERSIONING.md
  lgpd.md
  exposure-policy.md
  entity-resolution.md
```

Decisões de implementação que diferem do esboço inicial deste rascunho:

- **Schema único** `schema/mbras.schema.json` com `$defs`, em vez de um diretório `schemas/` com um arquivo por entidade.
- **Um exemplo canônico** (`examples/property.sample.json`) em vez de vários `*.example.json`.
- **OpenAPI mínimo** `openapi.yaml`, com endpoints de referência para `Unit`, `Property`, `Listing`, `ExposurePolicy` e índice de conformidade.
- **Runners de verificação** em `scripts/`: `validate_conformance.py` valida cada `payload` contra o `schema_ref`, avalia as `expected_decisions` da `ExposurePolicy` e barra vazamento de preço no feed; `validate_openapi.py` valida a estrutura mínima do OpenAPI e seus `$ref`.
- `docs/manifesto.md` e `docs/mvp.md` **não foram criados**; manifesto e MVP vivem nas seções deste documento (§18 e §14).

Ainda pendente para promover a v0.2 estável (detalhamento em `docs/REVIEW-FOLLOWUP.md`): RFC formal e transição para o estado "Aceito"; ampliar a superfície OpenAPI além do mínimo; e `PolicyDecisionResult`/`applied_rule_ids` no schema.

Isso impede que v0.1, v0.1.0 técnica e v0.2 continuem divergindo, e deixa explícito o que falta antes do corte de um padrão estável.

---

# 21. Referências técnicas

Referências verificadas para orientar o mapeamento inicial:

- RESO Data Dictionary: https://www.reso.org/data-dictionary/
- RESO Data Dictionary links and specifications: https://www.reso.org/knowledge-base/data-dictionary-wiki-and-specifications/
- OpenImmo: https://www.openimmo.org/
- OpenImmo download and XML schema information: https://www.openimmo.de/go.php/p/24/download.htm
- schema.org RealEstateListing: https://schema.org/RealEstateListing

Essas referências não substituem o desenho brasileiro. Elas reduzem risco, aumentam credibilidade técnica e ajudam o PIBRAS a nascer como adaptação consciente, não como reinvenção isolada.
