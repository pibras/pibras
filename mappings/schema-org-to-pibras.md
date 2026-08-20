# PIBRAS -> schema.org

schema.org é alvo de **publicação web e SEO**, não modelo canônico.

## Uso

- páginas públicas de imóveis;
- páginas de empreendimentos;
- dados estruturados para buscadores.

## Regra de governança

A projeção schema.org deriva **exclusivamente** do limite público minimizado
`property_public` (`db/schema.sql`). Nunca de `property`, `unit` ou
`property_full`, que contêm matrícula, coordenadas exatas, scores internos e
preço não filtrado. A view exige um `Listing` explicitamente público e aplica
minimização estrutural; decisões contextuais adicionais continuam sujeitas ao
`ExposurePolicyEvaluator` antes do envio.

Consequência normativa: se um campo não existe em `property_public`, ele
**não pode** aparecer na saída schema.org. O exportador não tem acesso ao
dado; a impossibilidade é estrutural, não uma regra que o implementador
precise lembrar de aplicar.

## Fonte normativa

| Item | Valor |
|---|---|
| Vocabulário | schema.org |
| Versão | **V30.0** |
| Data da versão | 2026-03-19 |
| Data de consulta | 2026-07-26 |
| Tipos consultados | [`RealEstateListing`](https://schema.org/RealEstateListing), [`Accommodation`](https://schema.org/Accommodation), [`Offer`](https://schema.org/Offer), [`ItemAvailability`](https://schema.org/ItemAvailability), [`BusinessFunction`](https://schema.org/BusinessFunction) |

### Decisão estrutural: por que não só `RealEstateListing`

`RealEstateListing` tem hierarquia `Thing > CreativeWork > WebPage`. É uma
**página**, não um lugar: define apenas `datePosted` e `leaseLength`. Não
possui `numberOfBedrooms`, `floorSize` nem endereço.

Portanto a projeção usa três nós:

```txt
RealEstateListing (a página do anúncio)
  ├─ mainEntity -> Accommodation (o imóvel físico)
  │                  └─ address, geo, floorSize, numberOfBedrooms, ...
  └─ offers     -> Offer (preço e função comercial)
```

Publicar dados físicos diretamente em `RealEstateListing` seria inválido no
vocabulário, ainda que buscadores tolerem.

## De/Para campo a campo

Origem: `property_public`. Alvo: schema.org V30.0.

| PIBRAS (`property_public`) | schema.org | Nó | Classificação | Observação |
|---|---|---|---|---|
| `id` | `identifier` | Accommodation | exato | UUID canônico |
| `code` | — | — | omitido | Código interno; não é identificador público estável |
| `property_type` | `@type` + `accommodationCategory` | Accommodation | **lossy** | Ver crosswalk de enums |
| `transaction_type` | `businessFunction` | Offer | **lossy** | `sale_rent`/`season_rent` sem equivalente |
| `property_status` | `availability` | Offer | **lossy** | Ver crosswalk de enums |
| `availability` | — | — | omitido | Redundante com `property_status` na borda pública |
| `asking_price_amount` | `price` | Offer | **condicional** | Só quando `price_display = 'visible'`; centavos -> `Text` decimal exato, sem `float` |
| `asking_price_currency` | `priceCurrency` | Offer | exato | ISO 4217 |
| `usable_area_m2` | `floorSize` (`QuantitativeValue`, `unitCode: MTK`) | Accommodation | exato | UN/CEFACT MTK = m² |
| `total_area_m2` | — | — | **omitido** | `floorSize` é cardinalidade 1; área útil é a mais comparável |
| `bedrooms` | `numberOfBedrooms` | Accommodation | exato | |
| `suites` | — | — | **omitido** | Sem equivalente; suíte é conceito brasileiro |
| `bathrooms` | `numberOfBathroomsTotal` | Accommodation | exato | Integer |
| `parking_spaces` | `amenityFeature` | Accommodation | **lossy** | `Accommodation` não define propriedade de vaga |
| `sun_orientation` | `amenityFeature` | Accommodation | **lossy** | Idem |
| `view_type` | `amenityFeature` | Accommodation | **lossy** | Idem |
| `city` | `addressLocality` | PostalAddress | exato | |
| `state` | `addressRegion` | PostalAddress | exato | UF |
| `neighborhood_id` | — | — | **omitido** | UUID interno; sem nome resolvido em `property_public` |
| `latitude_approx` | `latitude` | GeoCoordinates | **degradado** | Já arredondado (~1 km) na origem quando a política exige |
| `longitude_approx` | `longitude` | GeoCoordinates | **degradado** | Idem |
| `building_name` | `name` | Accommodation | exato | |
| `amenities` | `amenityFeature[]` | Accommodation | **lossy** | Texto é preservado, mas não há vocabulário controlado compartilhado |
| `updated_at` | `datePosted` | RealEstateListing | **aproximado** | `datePosted` é publicação; `updated_at` é última alteração |

Campos **ausentes por construção** (não existem em `property_public`, logo
nunca são publicáveis): `matricula`, coordenadas exatas, `liquidity_score`,
`match_score`, `rarity_score`, `off_market_potential`, dados de proprietário,
documentos, endereço completo (logradouro e número).

## Crosswalk de enums

### `property_type` -> `@type` + `accommodationCategory`

schema.org só oferece `Apartment`, `House`, `Room`, `Suite` e `CampingPitch`
como subtipos de `Accommodation`. O tipo brasileiro é preservado sem perda em
`accommodationCategory` (Text livre).

| PIBRAS | `@type` | `accommodationCategory` | Classificação |
|---|---|---|---|
| `apartment` | `Apartment` | `apartment` | exato |
| `penthouse` | `Apartment` | `penthouse` | lossy (cobertura vira apartamento) |
| `studio` | `Apartment` | `studio` | lossy |
| `loft` | `Apartment` | `loft` | lossy |
| `flat` | `Apartment` | `flat` | lossy |
| `house` | `House` | `house` | exato |
| `house_condo` | `House` | `house_condo` | lossy (casa em condomínio) |
| `land` | `Accommodation` | `land` | lossy (terreno não é acomodação) |
| `farm` | `Accommodation` | `farm` | lossy |
| `commercial_room` | `Accommodation` | `commercial_room` | lossy |
| `commercial_building` | `Accommodation` | `commercial_building` | lossy |
| `warehouse` | `Accommodation` | `warehouse` | lossy |
| `hotel` | `Accommodation` | `hotel` | lossy |
| `whole_building` | `Accommodation` | `whole_building` | lossy |
| `other` | `Accommodation` | `other` | lossy |

O `@type` é lossy por design; `accommodationCategory` é o campo que garante
round-trip semântico.

### `property_status` -> `availability` (`ItemAvailability`)

Membros verificados: `BackOrder`, `Discontinued`, `InStock`, `InStoreOnly`,
`LimitedAvailability`, `MadeToOrder`, `OnlineOnly`, `OutOfStock`, `PreOrder`,
`PreSale`, `Reserved`, `SoldOut`.

| PIBRAS | `availability` | Classificação |
|---|---|---|
| `available` | `InStock` | **aproximado** — disponibilidade imobiliária não é estoque de produto |
| `reserved` | `Reserved` | **aproximado** — os ciclos comerciais não são equivalentes |
| `under_offer` | `LimitedAvailability` | lossy |
| `sold` | `SoldOut` | **lossy** — disponibilidade não preserva a natureza da transação |
| `rented` | `SoldOut` | **lossy** — `ItemAvailability` não distingue vendido de alugado |
| `suspended` | `OutOfStock` | lossy |
| `draft` | *não publicado* | n/a |
| `off_market` | *não publicado* | n/a |
| `archived` | *não publicado* | n/a |

`draft`, `off_market` e `archived` nunca chegam ao exportador: `property_public`
filtra por `published = true` e listing publicado.

### `transaction_type` -> `businessFunction` (GoodRelations)

Membros verificados (prefixo `http://purl.org/goodrelations/v1#`): `Sell`,
`Buy`, `LeaseOut`, `Dispose`, `Maintain`, `Repair`, `ProvideService`,
`ConstructionInstallation`.

| PIBRAS | `businessFunction` | Classificação |
|---|---|---|
| `sale` | `Sell` | exato |
| `rent` | `LeaseOut` | exato |
| `sale_rent` | `Sell` + `LeaseOut` (dois `Offer`) | **lossy na leitura** |
| `season_rent` | `LeaseOut` | **lossy** — temporada não distinguível de locação comum |

`sale_rent` emite dois nós `Offer`. Um leitor que colapse ofertas não
reconstrói o valor original — daí a perda ser declarada.

## Round-trip: definição

Round-trip aqui significa **preservação da semântica declarada do PIBRAS**,
não reconstrução byte-a-byte. A saída schema.org é uma projeção pública
deliberadamente reduzida; reconstruir o registro completo seria justamente a
falha de exposição que o padrão evita.

Um campo é *round-trippable* quando o valor PIBRAS original pode ser
recuperado a partir da saída sem consultar a origem. `scripts/export_schema_org.py --round-trip`
verifica exatamente esse conjunto.

Campos declaradamente **não** round-trippable, e por quê:

| Campo | Motivo |
|---|---|
| `total_area_m2` | omitido (`floorSize` é cardinalidade 1) |
| `suites` | omitido (sem equivalente no vocabulário) |
| `neighborhood_id` | omitido (identificador interno) |
| `latitude_approx` / `longitude_approx` | degradação intencional na origem |
| `updated_at` | `datePosted` tem semântica diferente |
| `property_status = rented` | colide com `sold` em `SoldOut` |
| `transaction_type = season_rent` | colide com `rent` em `LeaseOut` |
| `property_type` (`@type`) | recuperável só via `accommodationCategory` |

## Conformidade

- Exportador: `scripts/export_schema_org.py`
- Fixtures: `tests/golden/schema-org.*.json`
- Casos: `tests/golden/conformance-cases.json` (`validator: "schema-org"`)
- Gate: `uv run scripts/validate_conformance.py` executa exportação, round-trip, preço decimal exato, rejeição de campos restritos e estados não publicáveis.
