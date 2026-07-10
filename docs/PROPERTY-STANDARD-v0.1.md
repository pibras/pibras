# Padrão MBRAS de Dados Imobiliários

> Status: historical and non-authoritative


**Property Inventory Hub — Modelo Canônico**
Versão 0.1.0 · 2026-06-18 · Status: rascunho para revisão

---

## 1. Propósito

Este documento define o **modelo canônico** do MBRAS Property Inventory Hub: o vocabulário único
("esperanto") para o qual todo sistema externo — Kenlo, Vista, Jetimob, Imobzi, Tecimob, portais,
XMLs, planilhas, APIs legadas — é traduzido na entrada e a partir do qual todo canal de distribuição
é alimentado na saída.

Regra fundadora: **nenhum dado proprietário pode ser destruído por integração externa.** Dados
externos entram como *sugestão* ou *atualização pendente*; viram padrão MBRAS apenas após validação;
campos sensíveis exigem aprovação.

Tudo aqui é fonte de verdade da baseline técnica v0.1.0 para os artefatos derivados:

| Artefato | Arquivo | Papel |
|---|---|---|
| Especificação (este doc) | `docs/MBRAS-PROPERTY-STANDARD.md` | Dicionário de referência do time |
| JSON Schema | `schema/mbras.schema.json` | Contrato formal — API pública e validação de ingestão |
| TypeScript / Zod | `types/mbras.ts` | Validadores e tipos para o backend |
| DDL Postgres | `db/schema.sql` | Tabelas reais (Neon / Directus), histórico e governança |
| Exemplo | `examples/property.sample.json` | Instância de referência validável |

> Nota de transição v0.2: `docs/PIBRAS-STANDARD-v0.2-draft.md` e
> `mappings/v0.1.0-code-to-v0.2.md` definem a reconciliação proposta. A baseline v0.1.0 continua
> compatível até que o draft seja promovido por RFC e todos os artefatos sejam atualizados juntos.

Convenções: nomes de campo em `snake_case`; identificadores `uuid`; datas/instantes em **ISO 8601 UTC**;
dinheiro como `{ amount: number, currency: enum }` com `amount` em unidade inteira da moeda (centavos);
áreas em m² (`numeric`); coordenadas em graus decimais (WGS84).

---

## 2. Decisões de arquitetura

### 2.1 Property ≠ Listing (ativo físico vs. anúncio)

A entidade física e a forma como ela aparece num canal são coisas distintas. O mesmo imóvel pode ter,
ao mesmo tempo, um anúncio público com preço, um anúncio *off-market* sem fachada e um anúncio
internacional cotado em dólar. Modelar `Listing` separado de `Property` é o que torna isso possível
sem duplicar o ativo.

### 2.2 Hierarquia Building → Unit → Property

Três identidades com tempos de vida diferentes:

- **Building / Condomínio** — o empreendimento físico compartilhado (nome, endereço, áreas comuns,
  amenities, mídia do condomínio, incorporadora). Opcional: casa e terreno não têm Building.
- **Unit** — a **identidade física durável** da unidade: matrícula, área, dormitórios, suítes, vagas,
  andar, posição solar, vista. Existe independentemente de estar à venda. Pertence a 0..1 Building.
  Para casa/terreno, a `Unit` carrega o próprio endereço.
- **Property** — o **registro comercial de inventário**: vincula-se a exatamente uma `Unit`, e adiciona
  proprietário, preço pedido, status, regra de exposição, inteligência e ciclo de vida. É "o que a MBRAS
  tem na carteira".

Por que isso importa para a MBRAS: a deduplicação correta acontece no nível da **Unit** (mesma matrícula
/ mesmo endereço+área = mesma unidade física), enquanto a mesma unidade pode ter **vários** `Property`
ao longo dos anos (vendida duas vezes, dois proprietários, dois históricos de preço). A `Unit` é a
âncora de identidade; o `Property` é o engajamento comercial atual.

> **MVP pragmático:** na ingestão, `Unit` e `Property` são criados juntos (1:1). A deduplicação tenta
> casar a `Unit` recebida com uma existente por matrícula → endereço normalizado + área → geo + specs.
> A informação comercial nova se anexa como `Property` novo/atualizado sobre a `Unit` casada.

### 2.3 Proveniência em todo registro

Toda entidade primária carrega um bloco `provenance` (sistema de origem, id externo, quando/quem
ingeriu, *trust tier*, lote de sync). Isso permite auditar de onde veio cada dado e resolver conflitos.

### 2.4 Hierarquia de confiança (resolução de conflito)

Quando duas origens divergem sobre o mesmo campo, vence a de **menor** `trust_tier`. O hub **nunca**
sobrescreve automaticamente dado de tier mais confiável com dado de tier menos confiável — gera item
na fila de conflito.

| Tier | Origem | Observação |
|---|---|---|
| 1 | `diretoria_approved` | Decisão manual aprovada pela diretoria |
| 2 | `mbras_internal` | Sistema/curadoria interna MBRAS |
| 3 | `twenty_crm` | Operação comercial (TwentyCRM) |
| 4 | `external_primary` | Sistema externo principal (ex.: Kenlo/Vista) |
| 5 | `xml_feed` | Feed XML de portal |
| 6 | `spreadsheet_import` | Planilha importada |

### 2.5 Governança de ingestão (estado do registro)

Todo registro primário tem `record_state`:

`draft` · `pending_review` · `active` · `conflict` · `duplicate` · `rejected` · `archived`

Fluxo: conector → `ingestion_record` (payload bruto) → candidato mapeado+normalizado → dedupe/match →
se tier alto e sem conflito → *upsert* canônico (com audit) ; senão → `pending_change` / fila de
conflito → aprovação humana → aplica.

### 2.6 Segurança a nível de campo

Para altíssimo padrão e *off-market*, não basta esconder o imóvel inteiro. A `ExposureRule` define,
por campo, o papel mínimo para visualizar. Ex.: com `exposure_level = confidential`, a API retorna
`null` em `address.number` e em `owner` a menos que o token seja de Diretor. Ver §6.

---

## 3. Mapa de entidades

```txt
Building (0..1) ──< Unit (1) ──1:1── Property ──1:1── PropertyIntelligence
                      │                  │
                      │                  ├──< Listing >── PublicationChannel
                      │                  ├──< property_owners >── Owner
                      │                  ├──< property_brokers >── Broker
                      │                  ├──< MediaAsset (também em Building/Unit)
                      │                  ├──< Document
                      │                  ├──< PriceHistory / StatusHistory
                      │                  ├──< ExposureRule
                      │                  ├──< LeadInterest / Visit / Offer
                      │                  └──< ComparableProperty
                   Neighborhood (referência normalizada para Address)
                   audit_log (genérico, todas as entidades)
```

Entidades primárias: **Building, Unit, Property, PropertyIntelligence, Listing, Owner, Broker,
MediaAsset, Document, PublicationChannel, LeadInterest, Visit, Offer, ExposureRule,
ComparableProperty, Neighborhood**. Mais as trilhas **PriceHistory, StatusHistory** e o **audit_log**
genérico.

---

## 4. Tipos compartilhados

### 4.1 `Provenance` (embutido em toda entidade primária)

| Campo | Tipo | Obrig. | Descrição |
|---|---|---|---|
| `source_system` | enum `source_system` | sim | Sistema de origem do dado |
| `source_record_id` | string | não | Código/ID do registro no sistema de origem |
| `source_url` | string (uri) | não | Link de origem, quando houver |
| `trust_tier` | int 1–6 | sim | Confiança da origem (§2.4) |
| `ingested_at` | datetime | sim | Quando entrou no hub |
| `ingested_by` | string | não | Usuário/conector responsável |
| `sync_batch_id` | uuid | não | Lote de sincronização |
| `raw_payload_ref` | string | não | Ponteiro para o payload bruto em `ingestion_record` |

### 4.2 `Money`

`{ amount: integer (centavos), currency: enum currency }` — ex.: `R$ 17.500.000,00` → `{ amount: 1750000000, currency: "BRL" }`.

### 4.3 `Address`

| Campo | Tipo | Notas |
|---|---|---|
| `street` | string | Logradouro |
| `number` | string | Número (mascarável por exposição) |
| `complement` | string | Apto/bloco/sala |
| `neighborhood_id` | uuid → Neighborhood | Bairro normalizado |
| `neighborhood_raw` | string | Texto original recebido (auditoria) |
| `city` | string | |
| `state` | string(2) | UF |
| `postal_code` | string | CEP |
| `country` | string(2) | ISO 3166-1, default `BR` |
| `latitude` / `longitude` | number | WGS84 |
| `geo_precision` | enum | `exact` · `approximate` · `neighborhood` · `none` |
| `formatted` | string | Endereço formatado (derivado) |

### 4.4 `AuditStamp` (em toda entidade primária)

`created_at`, `updated_at` (datetime) · `created_by`, `updated_by` (string) · `version` (int, incrementa a cada gravação) · `record_state` (enum, §2.5) · `completeness_score` (0–100, calculado) · `data_quality` (objeto: campos faltantes, avisos).

---

## 5. Enums canônicos

| Enum | Valores |
|---|---|
| `source_system` | `mbras_internal`, `twenty_crm`, `kenlo`, `vista`, `jetimob`, `imobzi`, `tecimob`, `orulo`, `zap_vivareal`, `olx`, `xml_generic`, `csv_import`, `excel_import`, `manual`, `other` |
| `trust_tier` | `1`..`6` (§2.4) |
| `record_state` | `draft`, `pending_review`, `active`, `conflict`, `duplicate`, `rejected`, `archived` |
| `property_type` | `apartment`, `penthouse`, `house`, `house_condo`, `studio`, `loft`, `flat`, `land`, `farm`, `commercial_room`, `commercial_building`, `warehouse`, `hotel`, `whole_building`, `other` |
| `transaction_type` | `sale`, `rent`, `sale_rent`, `season_rent` |
| `property_status` | `draft`, `available`, `reserved`, `under_offer`, `sold`, `rented`, `suspended`, `off_market`, `archived` |
| `availability` | `available`, `unavailable`, `conditioned` |
| `currency` | `BRL`, `USD`, `EUR` |
| `exposure_level` | `public`, `restricted`, `confidential`, `off_market` |
| `confidentiality` | `normal`, `sensitive`, `highly_confidential` |
| `media_type` | `photo`, `video`, `floor_plan`, `virtual_tour`, `document`, `aerial` |
| `media_role` | `cover`, `gallery`, `floor_plan`, `facade`, `common_area`, `view`, `amenity`, `other` |
| `media_rights` | `owned`, `licensed`, `restricted` |
| `channel_type` | `website`, `portal`, `crm`, `broker_network`, `off_market_pdf`, `paid_ad`, `landing_page`, `whatsapp`, `email` |
| `owner_type` | `individual`, `company` |
| `owner_role` | `owner`, `representative`, `heir`, `attorney` |
| `broker_role` | `listing`, `co_listing`, `capture` |
| `document_type` | `matricula`, `iptu`, `contrato`, `escritura`, `laudo_avaliacao`, `planta_aprovada`, `habite_se`, `other` |
| `listing_status` | `draft`, `published`, `paused`, `expired`, `removed` |
| `price_display` | `visible`, `on_request` |
| `address_display` | `full`, `approximate`, `hidden` |
| `lead_stage` | `new`, `qualified`, `engaged`, `negotiating`, `won`, `lost` |
| `visit_status` | `scheduled`, `done`, `no_show`, `cancelled` |
| `offer_status` | `submitted`, `countered`, `accepted`, `rejected`, `withdrawn` |
| `sun_orientation` | `morning`, `afternoon`, `full_day`, `none` |
| `building_status` | `planning`, `under_construction`, `ready` |

---

## 6. Entidades

> Convenção das tabelas abaixo: **O** = obrigatório. Todos os primários incluem implicitamente
> `id (uuid)`, `provenance` (§4.1) e `AuditStamp` (§4.4), omitidos para não repetir.

### 6.1 Building / Condomínio

| Campo | Tipo | O | Descrição |
|---|---|:--:|---|
| `name` | string | ✓ | Nome do empreendimento |
| `developer` | string | | Incorporadora |
| `address` | Address | ✓ | Endereço do condomínio |
| `building_status` | enum | | `planning`/`under_construction`/`ready` |
| `year_built` | int | | Ano de entrega/construção |
| `delivery_date` | date | | Previsão de entrega (lançamentos) |
| `floors` | int | | Nº de andares |
| `towers` | int | | Nº de torres |
| `total_units` | int | | Unidades totais |
| `amenities` | string[] | | Lazer/serviços (piscina, academia, …) |
| `description` | string | | Texto descritivo |

> Mídia de área comum vincula-se ao Building e é **herdada** pelos Listings das suas Units — evita
> duplicar 20 fotos de lazer em cada apartamento à venda no prédio.

### 6.2 Unit

| Campo | Tipo | O | Descrição |
|---|---|:--:|---|
| `building_id` | uuid → Building | | Nulo para casa/terreno |
| `matricula` | string | | Matrícula do registro de imóveis (chave durável) |
| `property_type` | enum | ✓ | Tipo físico |
| `address` | Address | | Próprio endereço (casa/terreno); senão herda do Building |
| `unit_number` | string | | Nº da unidade |
| `tower` | string | | Torre/bloco |
| `floor` | int | | Andar |
| `usable_area_m2` | numeric | | Área útil/privativa |
| `total_area_m2` | numeric | | Área total |
| `lot_area_m2` | numeric | | Área do terreno |
| `bedrooms` | int | | Dormitórios |
| `suites` | int | | Suítes |
| `bathrooms` | int | | Banheiros |
| `parking_spaces` | int | | Vagas |
| `sun_orientation` | enum | | Posição solar |
| `view_type` | string | | Tipo de vista |
| `ceiling_height_m` | numeric | | Pé-direito |
| `features` | string[] | | Características da unidade |
| `condo_fee` | Money | | Valor de condomínio |
| `iptu_annual` | Money | | IPTU anual |

### 6.3 Property (registro de inventário)

| Campo | Tipo | O | Descrição |
|---|---|:--:|---|
| `code` | string | | Código MBRAS legado/compatibilidade (ex.: `MB18495`); o alvo canônico é `external_ids[]` |
| `unit_id` | uuid → Unit | ✓ | Unidade física |
| `building_id` | uuid → Building | | Conveniência (denormalizado da Unit) |
| `transaction_type` | enum | ✓ | Venda/locação |
| `property_status` | enum | ✓ | Status comercial |
| `availability` | enum | | Disponibilidade |
| `asking_price` | Money | | Preço pedido |
| `min_accepted_price` | Money | | Valor mínimo aceito (sensível) |
| `rent_price` | Money | | Aluguel (se locação) |
| `exclusive` | bool | | Exclusividade MBRAS |
| `exclusivity_until` | date | | Fim da exclusividade |
| `headline` | string | | Título interno do ativo |
| `summary` | string | | Resumo interno |
| `primary_broker_id` | uuid → Broker | | Corretor responsável |
| `published` | bool | | Há ao menos 1 Listing publicado |
| `last_price_change_at` | datetime | | Conveniência (deriva de PriceHistory) |

Relações: `property_owners` (N:N com Owner) · `property_brokers` (N:N com Broker) · `Listing` (1:N) ·
`MediaAsset` (1:N) · `Document` (1:N) · `ExposureRule` (1:N) · `PriceHistory`/`StatusHistory` (1:N) ·
`PropertyIntelligence` (1:1).

### 6.4 PropertyIntelligence (camada premium — 1:1 com Property)

A vantagem competitiva. Pode ser calculada/atualizada pela *Intelligence Layer* (Hermes/agent) com
controle de acesso próprio.

| Campo | Tipo | Descrição |
|---|---|---|
| `ideal_buyer_profile` | string | Perfil ideal de comprador |
| `likely_objections` | string[] | Objeções prováveis |
| `selling_arguments` | string[] | Argumentos comerciais |
| `privacy_level` | string | Nível de privacidade do imóvel |
| `rarity_score` | int 0–100 | Raridade |
| `architecture_notes` | string | Arquitetura |
| `view_quality` | int 0–100 | Vista |
| `natural_light` | int 0–100 | Luz natural |
| `noise_level` | int 0–100 | Silêncio (maior = mais silencioso) |
| `liquidity_score` | int 0–100 | Liquidez estimada |
| `match_score` | int 0–100 | Aderência média à demanda atual |
| `defensible_price` | Money | Preço defensável |
| `off_market_potential` | int 0–100 | Potencial off-market |
| `demand_notes` | string | Observações de demanda por bairro |
| `last_computed_at` | datetime | Último cálculo |
| `computed_by` | enum | `human` · `agent` · `hermes` |
| `confidence` | int 0–100 | Confiança do cálculo |

### 6.5 Listing (anúncio por canal)

Um `Property` pode ter vários `Listing` — um por canal/idioma/moeda.

| Campo | Tipo | O | Descrição |
|---|---|:--:|---|
| `property_id` | uuid → Property | ✓ | Ativo de origem |
| `channel_id` | uuid → PublicationChannel | ✓ | Canal de publicação |
| `locale` | string | ✓ | `pt-BR`, `en-US`, … |
| `transaction_type` | enum | ✓ | Venda/locação para este anúncio |
| `title_public` | string | | Título exibido |
| `title_internal` | string | | Título interno |
| `description_public` | string | | Descrição exibida |
| `description_internal` | string | | Descrição interna |
| `price_display` | enum | ✓ | `visible` / `on_request` |
| `display_price` | Money | | Preço exibido (pode diferir do `asking_price`, ex.: USD) |
| `address_display` | enum | ✓ | `full` / `approximate` / `hidden` |
| `media_selection` | uuid[] | | Subconjunto ordenado de MediaAsset permitido neste canal |
| `listing_status` | enum | ✓ | `draft`/`published`/`paused`/`expired`/`removed` |
| `exposure_level` | enum | | Sobrescreve o do Property, se necessário |
| `published_at` | datetime | | |
| `expires_at` | datetime | | |
| `external_listing_id` | string | | ID do anúncio no canal externo |
| `external_url` | string (uri) | | URL pública do anúncio |

### 6.6 Owner (proprietário — PII sensível)

| Campo | Tipo | O | Descrição |
|---|---|:--:|---|
| `owner_type` | enum | ✓ | `individual`/`company` |
| `name` | string | ✓ | Nome/razão social |
| `legal_name` | string | | Razão social formal |
| `tax_id` | string | | CPF/CNPJ (**altamente confidencial**) |
| `email` | string | | |
| `phone` | string | | |
| `whatsapp` | string | | |
| `address` | Address | | |
| `preferred_contact` | string | | |
| `marketing_consent` | bool | | LGPD |
| `notes` | string | | |

Vínculo `property_owners`: `property_id`, `owner_id`, `ownership_pct` (numeric), `owner_role` (enum), `is_primary` (bool).

### 6.7 Broker (corretor)

`name` (✓), `creci`, `email`, `phone`, `team`, `active` (bool). Vínculo `property_brokers`:
`property_id`, `broker_id`, `broker_role` (enum), `is_primary` (bool), `assigned_at`.

### 6.8 MediaAsset

| Campo | Tipo | O | Descrição |
|---|---|:--:|---|
| `scope` | enum | ✓ | `building` / `unit` / `property` / `listing` |
| `building_id` / `unit_id` / `property_id` | uuid | | Conforme o escopo |
| `media_type` | enum | ✓ | |
| `media_role` | enum | ✓ | |
| `url` | string (uri) | ✓ | |
| `storage_key` | string | | Chave no storage |
| `width` / `height` | int | | Pixels |
| `duration_s` | int | | Vídeo |
| `order_index` | int | | Ordenação |
| `caption` | string | | |
| `media_rights` | enum | | `owned`/`licensed`/`restricted` |
| `visibility` | enum exposure_level | | |
| `is_cover` | bool | | |
| `checksum` | string | | Hash perceptual/MD5 para dedupe |
| `ai_tags` | string[] | | Tags geradas por IA |

### 6.9 Document

`scope` (`property`/`unit`/`owner`), `*_id`, `document_type` (enum, ✓), `title`, `url`, `storage_key`,
`confidentiality` (enum, default `sensitive`), `valid_until` (date).

### 6.10 PublicationChannel

`key` (✓, ex.: `website_mbras`, `zap`, `vivareal`, `olx`, `broker_net`, `offmarket_pdf`, `meta_ads`),
`name` (✓), `channel_type` (enum, ✓), `config` (objeto), `active` (bool).

### 6.11 ExposureRule

`ExposureRule` permanece como compatibilidade v0.1.0. O alvo v0.2 é `ExposurePolicy`, com semântica
default-deny, precedência de deny explícito, decisão `needs_approval`, match de campos por caminho/prefixo
e retorno auditável por `reason_code`. A migração está descrita em `mappings/v0.1.0-code-to-v0.2.md`.

| Campo | Tipo | Descrição |
|---|---|---|
| `property_id` | uuid → Property | Alvo (ou regra default por nível) |
| `exposure_level` | enum | Nível |
| `field_visibility` | objeto | Mapa campo → papel mínimo. Ex.: `{"address.number":"director","owner":"broker"}` |
| `allowed_channels` | string[] | Chaves de canal permitidas |
| `price_display` | enum | |
| `address_display` | enum | |
| `requires_approval` | bool | Mudanças exigem aprovação |

**Defaults por nível** (aplicados quando não há regra específica):

| Nível | Preço | Endereço | Owner/Docs | Canais |
|---|---|---|---|---|
| `public` | visible | full | ocultos a não-internos | todos |
| `restricted` | visible | approximate | ocultos a não-internos | site + broker_net |
| `confidential` | on_request | hidden | só diretoria | broker_net + offmarket_pdf |
| `off_market` | on_request | hidden | só diretoria | offmarket_pdf |

### 6.12 LeadInterest · Visit · Offer

- **LeadInterest** — `property_id`, contato (`name`/`email`/`phone`), `lead_stage`, `score`,
  `match_score`, `source`, `crm_external_id`, `notes`. (A operação vive no TwentyCRM; aqui guardamos a referência e o match.)
- **Visit** — `property_id`, `lead_ref`, `broker_id`, `scheduled_at`, `visit_status`, `feedback`.
- **Offer** — `property_id`, `buyer_ref`, `amount` (Money), `offer_status`, `conditions`, `decided_at`.

### 6.13 PriceHistory · StatusHistory

- **PriceHistory** — `property_id`, `old_price` (Money), `new_price` (Money), `changed_by`,
  `source_system`, `trust_tier`, `reason`, `changed_at`.
- **StatusHistory** — `property_id`, `old_status` (enum), `new_status` (enum), `changed_by`,
  `source_system`, `reason`, `changed_at`.

Exemplo:
```txt
MB18495 · R$ 18.000.000 → R$ 17.500.000 · por Broker X · origem kenlo (tier 4) · 2026-06-18
```

### 6.14 ComparableProperty

`property_id` (sujeito), `address`, `area_m2`, `price` (Money), `sold_at`, `source`,
`similarity_score` (0–100), `notes`. Alimenta `defensible_price`.

### 6.15 Neighborhood (referência de normalização)

`canonical_name` (✓), `aliases` (string[] — ex.: `["Jd. Europa","Jardim Europa"]`), `city`, `state`,
`zone`, `centroid_lat`/`centroid_lng`, `polygon` (GeoJSON), `demand_index`, `avg_price_m2` (Money).

---

## 7. Padrão mínimo vs. padrão premium

**Mínimo obrigatório em qualquer importação** (senão o registro entra como `draft`/`pending_review`):
`provenance.source_system`, `property_type`, `address.city`, `address.neighborhood_raw`,
`transaction_type`, `property_status`, e ao menos um de (`asking_price` | `rent_price`).

**Premium MBRAS** (diferencial competitivo — bloco `PropertyIntelligence` + regras de exposição):
perfil ideal de comprador, objeções, argumentos, raridade, vista, luz, silêncio, liquidez, match,
preço defensável, potencial off-market, confidencialidade.

---

## 8. Normalização (Mapping + Validation Layer)

Toda entrada passa por normalização determinística antes do dedupe:

| Caso | Entrada | Saída canônica |
|---|---|---|
| Bairro | `Jd. Europa`, `V. Nova Conceição` | resolve para `Neighborhood` via `aliases` |
| Dinheiro | `R$ 12.000.000,00` | `{ amount: 1200000000, currency: "BRL" }` |
| Área | `740m2`, `740 m²` | `740` (numeric) |
| Booleano | `sim`/`não`, `S`/`N` | `true`/`false` |
| Endereço | `R. Oscar Freire, 1000` / `Rua Oscar Freire 1000` | normalização + geocodificação (Google/Correios) antes de comparar |

**Deduplicação (nível Unit):** matrícula → endereço normalizado + área → geo + (dormitórios, área, preço)
→ similaridade de fotos (checksum/embeddings) + similaridade de descrição (embeddings). Casos acima do
limiar entram como `duplicate` para revisão no Migration Studio, nunca apagados automaticamente.

**Quality score:** `completeness_score` (0–100) por registro, listando o que falta (planta, vídeo,
regra de exposição, perfil de comprador, valor de condomínio, …).

---

## 9. Versionamento e auditoria

Cada entidade primária tem `version` (incrementa a cada gravação) e gera linha em `audit_log`
(`entity_type`, `entity_id`, `field`, `old_value`, `new_value`, `change_type`, `source_system`,
`trust_tier`, `actor`, `occurred_at`, `sync_batch_id`). `PriceHistory` e `StatusHistory` são trilhas
dedicadas para os dois eventos mais consultados comercialmente.

---

## 10. Distribuição (resumo)

Escrita (pesada: validação, dedupe, audit) é separada da leitura (rápida). O write model é o Postgres
canônico; um read model (ex.: Elasticsearch/materialized view `property_full`) serve site, portais e
CRM. A `ExposureRule` é aplicada na borda de leitura, mascarando campos conforme o papel do token.

---

## 11. Changelog

- **0.2 draft (2026-06-19)** — Reconciliado com a visão PIBRAS aberta: preserva `Money` em centavos,
  `Building -> Unit -> Property`, e adiciona alvo para `external_ids`, `Organization/Tenant`,
  `Party/Ownership`, `ExposurePolicy`, `DataSubjectRequest` e testes golden.
- **0.1.0 (2026-06-18)** — Primeira versão do modelo canônico: entidades, enums, tipos compartilhados,
  governança de ingestão, exposição a nível de campo e regras de normalização.
