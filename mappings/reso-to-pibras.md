# RESO -> PIBRAS

## Escopo MVP

O mapeamento RESO inicial deve ser limitado a:

- Property;
- Unit;
- Building/Condominium quando houver equivalência útil;
- MediaAsset;
- Listing/PublicationChannel;
- enums de tipo, status e transação.

## Regra

PIBRAS não importa enums RESO cegamente. Usa enums próprios quando o mercado
brasileiro, LGPD, portais ou off-market exigirem diferença clara.

---

# Registro de decisões (P4b)

> **Status: BLOQUEADO — pendente de parecer jurídico.**
> Este registro documenta a investigação. Nenhum crosswalk RESO executável foi
> publicado, e nenhum valor RESO foi inventado.

## 1. Acesso à fonte autoritativa

| Item | Valor |
|---|---|
| Fonte canônica | <https://dd.reso.org/> (`ddwiki.reso.org` redireciona 301) |
| Credenciais | **Não exigidas.** Leitura pública e anônima |
| Versão vigente | **DD 2.0**, aprovada em 2023-10-23 |
| Também publicada | DD 1.7 |
| Data de consulta | 2026-07-26 |

Não verificado: datas de DD 2.1 e DD 3.0 (obtidas apenas de resumos de busca,
sem página oficial recuperada).

## 2. Bloqueio de licenciamento

O [RESO EULA](https://www.reso.org/eula/) estabelece que o licenciado:

- pode reproduzir e derivar **"solely for incorporation into End User's
  products or services"**;
- **não pode** "distribute, or display the RESO Standard" fora dessa
  incorporação;
- **não pode** "use RESO Standard to create a derivative work as a technical
  standard";
- não recebe licença de marca.

**Avaliação.** Publicar um crosswalk PIBRAS↔RESO — que necessariamente
reproduz valores de enum RESO — dentro de um padrão aberto sob Apache-2.0 /
CC BY 4.0 parece recair exatamente na cláusula que veda derivar um *technical
standard*. Isto é questão jurídica, não de engenharia.

**Ação requerida antes de qualquer publicação:** parecer jurídico ou
autorização escrita da RESO. Alternativas de menor risco, também a validar:

1. distribuir o crosswalk como código/config dentro de um produto
   (possivelmente coberto por "incorporation into End User's products");
2. publicar apenas os valores PIBRAS, referenciando os alvos RESO por URL sem
   reproduzir as listas.

Não verificado: se a RESO oferece licença distinta para mapeamento entre
padrões ou uso acadêmico; se os repositórios RESO no GitHub ou a Web API spec
carregam termos diferentes do EULA.

## 3. Achado estrutural

RESO **não possui campo de tipo de transação**. Venda e locação estão
embutidas no próprio `PropertyType`: `Residential`, `Commercial Sale`, `Farm`,
`Land`, `Business Opportunity` são venda; `Residential Lease` e
`Commercial Lease` são locação.

`PropertyType` é `String List Single` — **um valor por registro**. Um imóvel
PIBRAS com `transaction_type = sale_rent` exige, portanto, **dois registros
RESO distintos**. Não é perda de fidelidade de campo; é divergência de
cardinalidade entre os modelos.

## 4. Candidatos e classificação

Fontes: [DD 2.0 PropertyType](https://dd.reso.org/DD2.0/lookups/PropertyType/),
[DD 2.0 PropertySubType](https://dd.reso.org/DD2.0/lookups/PropertySubType/),
[DD 2.0 StandardStatus](https://dd.reso.org/DD2.0/lookups/StandardStatus/),
[DD 1.7 MlsStatus](https://dd.reso.org/DD1.7/Property/MlsStatus/).
Consulta: 2026-07-26.

### 4.1 `property_type`

| PIBRAS | Candidato RESO | Classificação |
|---|---|---|
| `apartment` | `Apartment` ou `Condominium` | **ambíguo** — RESO divide por estrutura de propriedade; PIBRAS por forma construtiva. "Apartamento" brasileiro costuma ser `Condominium` |
| `penthouse` | — | **sem alvo** |
| `house` | `Single Family Residence` | **limpo** |
| `house_condo` | — | **sem alvo** (ver §5) |
| `studio` / `loft` / `flat` | — | **sem alvo** |
| `land` | `Unimproved Land` | **lossy** — o valor RESO é definido como terreno *comercial* não edificado |
| `farm` | `Farm` / `Agriculture` / `Ranch` | **limpo** |
| `commercial_room` | `Office` ou `Retail` | **lossy** (ver §5) |
| `commercial_building` | `Mixed Use` / `Office` / `Retail` | **lossy** — exige comprometer-se com um uso |
| `warehouse` | `Warehouse` | **limpo** |
| `hotel` | `Hotel/Motel` | **limpo** |
| `whole_building` | `Multi Family` | **lossy** — só cobre residencial 5+ unidades |
| `other` | — | **sem alvo** |

### 4.2 `property_status`

| PIBRAS | Candidato RESO | Classificação |
|---|---|---|
| `draft` | `Incomplete` | **limpo** |
| `available` | `Active` | **limpo** |
| `reserved` | `Active Under Contract` ou `Hold` | **ambíguo** |
| `under_offer` | `Active Under Contract` / `Pending` | **ambíguo** — RESO separa on-market de off-market; PIBRAS não codifica isso |
| `sold` | `Closed` | **limpo** |
| `rented` | `Closed` | **lossy** — `Closed` cobre venda e locação; colide com `sold` |
| `suspended` | `Hold` | **lossy, defensável** |
| `off_market` | — | **sem alvo** (ver §5) |
| `archived` | — | **sem alvo** — `Delete` significa contrato inválido, não arquivamento |

### 4.3 `transaction_type`

| PIBRAS | Situação |
|---|---|
| `sale` | limpo, via `PropertyType` |
| `rent` | limpo, via `PropertyType` |
| `sale_rent` | **sem alvo** — exige dois registros RESO |
| `season_rent` | **sem alvo** — não há valor de locação por temporada |

## 5. Decisões que exigem aprovação de domínio

Nenhuma destas pode ser resolvida por inferência.

| # | Questão | Recomendação |
|---|---|---|
| D1 | **Licenciamento.** Um crosswalk RESO pode ser publicado sob Apache-2.0/CC BY 4.0? | Obter parecer jurídico. **Bloqueia D2–D6.** |
| D2 | **`house_condo`.** Casa em condomínio fechado: RESO opõe `Condominium` (propriedade unitária) a `Single Family Residence` (casa em lote). A modalidade brasileira é frequentemente ambas. | Não mapear. Registrar como extensão PIBRAS; RESO não tem eixo de condomínio/HOA |
| D3 | **`off_market`.** Ausente das 11 `StandardStatus`. `Withdrawn`/`Hold`/`Canceled` carregam semântica contratual que `off_market` não afirma. | Usar `MlsStatus`, que é enumeração **aberta** por especificação, preservando `StandardStatus` compatível |
| D4 | **`sale_rent`.** Divergência de cardinalidade, não de vocabulário. | Emitir dois registros RESO com `external_ids[]` comum |
| D5 | **`season_rent`.** Sem valor de temporada. `Timeshare` é outro conceito (propriedade fracionada). | Mapear para locação e registrar a perda explicitamente |
| D6 | **`commercial_room`.** Sala comercial é unidade autônoma em edifício comercial — "condomínio de uso comercial", que RESO não expressa. | Escolher `Office` como padrão **é uma suposição de uso**, não tradução. Requer decisão de domínio |

## 6. Não verificado

- Definições textuais dos três valores novos da DD 2.0 (`Co-Ownership`,
  `Mobile Home Park`, `Tenancy in Common`).
- Restrições de validade entre `PropertyType` e `PropertySubType`: a
  documentação **não** publica quais subtipos são legais sob cada tipo.
  Qualquer crosswalk que afirme esses pares estaria inventando uma restrição.
- Precedente de mapeamento brasileiro por membros RESO: nenhum encontrado,
  ausência não confirmada.
