# PIBRAS — Portfólio Imobiliário do Brasil

> Status: historical and non-authoritative


**Consolidação completa dos conceitos discutidos — Documento fundador**

Versão: v0.1 · Data: 18 de junho de 2026
Origem: consolidação da conversa sobre Hermes Agent, TwentyCRM, Windmill, Property Inventory Hub,
Property Matching Engine, sistemas nacionais, APIs, migração de dados, stack open-source e criação do PIBRAS.

> Este é o documento de visão/padrão fundador do projeto. Os artefatos técnicos do modelo canônico
> (`schema/`, `types/`, `db/`, `examples/`) devem ser alinhados às convenções definidas aqui.
> **Princípio central: PIBRAS é o padrão. A stack é apenas uma forma de implementar.**

---

## 1. Visão geral

A conversa começou com uma pergunta simples:

> Hermes Agent + TwentyCRM, dá para organizar meu CRM combinando os dois?

A resposta evoluiu para uma arquitetura muito maior. A ideia inicial era combinar TwentyCRM como
sistema de registro comercial; Hermes Agent como operador inteligente; uma camada de automação; uma
base de dados confiável; dashboards; e, depois, um inventário estruturado de imóveis.

A partir disso, surgiu a necessidade de algo maior do que um CRM ou um cadastro de imóveis: um hub
imobiliário proprietário, capaz de organizar inventário, importar dados, conversar com sistemas
nacionais, preparar dados para IA e permitir migrações. Esse hub recebeu o nome **PIBRAS, Portfólio
Imobiliário do Brasil**.

A conclusão mais importante é: **PIBRAS não é a stack. PIBRAS é o padrão.** A stack recomendada pode
incluir TwentyCRM, Windmill, Directus, Postgres, Hermes Agent e Metabase, mas ela deve ser opcional.
Quem quiser usar tudo, usa. Quem já tem sistemas próprios pode usar apenas o PIBRAS Standard, a API,
os conectores ou o Migration Studio.

## 2. O que é PIBRAS

PIBRAS significa **Portfólio Imobiliário do Brasil**: uma iniciativa aberta para organizar,
padronizar, importar, normalizar, enriquecer e distribuir dados imobiliários no Brasil. Deve funcionar
como camada comum entre imobiliárias, incorporadoras, CRMs, ERPs, portais, sites próprios, sistemas
nacionais, bancos de dados, planilhas, XMLs, APIs, ferramentas de IA, ferramentas de BI,
desenvolvedores e parceiros do segmento. A proposta não é substituir os sistemas existentes, e sim
permitir que todos conversem melhor.

- **Frase central:** PIBRAS é uma infraestrutura aberta para organizar, migrar, integrar e distribuir dados imobiliários no Brasil.
- **Frase institucional:** PIBRAS, Portfólio Imobiliário do Brasil, é uma iniciativa aberta para criar um padrão nacional de dados imobiliários, conectando sistemas, portais, CRMs, incorporadoras, imobiliárias e desenvolvedores em torno de uma linguagem comum.
- **Frase para desenvolvedores:** PIBRAS é um padrão aberto e extensível para modelar imóveis, anúncios, mídias, proprietários, regras de exposição e integrações no mercado imobiliário brasileiro.

## 3. Separação dos conceitos

```txt
PIBRAS                    → o padrão aberto e o hub de interoperabilidade imobiliária
Stack recomendada         → uma forma sugerida de implementar o PIBRAS
Sistemas existentes       → ferramentas que podem se conectar ao PIBRAS
Conectores                → pontes entre o PIBRAS e sistemas do mercado
Migration Studio          → ferramenta para importar, migrar, limpar e normalizar dados
Property Matching Engine  → camada opcional de inteligência comercial sobre os dados organizados
```

**3.1 PIBRAS Standard** — o coração do projeto. Define: modelo canônico de dados imobiliários;
separação entre imóvel físico e anúncio; entidades principais; JSON Schema; OpenAPI; contratos de
importação; regras de validação; regras de visibilidade; padrão de conectores; padrão de migração;
nomenclatura comum; estrutura mínima para interoperabilidade. Deve ser independente de tecnologia
(Postgres, MySQL, MongoDB, Directus, Strapi, Laravel, NestJS, Django, Rails, sistemas próprios, CRMs
ou ERPs existentes). O importante é respeitar o padrão.

**3.2 PIBRAS Core** — a implementação open-source oficial inicial: API principal; banco de dados;
schemas; validações; importadores; deduplicação; controle de status; controle de mídia; controle de
exposição; logs; auditoria; permissões; endpoints internos e públicos.

**3.3 PIBRAS Studio** — interface de gestão, importação, migração e governança: gestão de imóveis;
revisão de dados; importação de CSV/Excel/XML/API; mapeamento visual de campos; validação;
deduplicação; relatórios de qualidade; aprovação humana; histórico de importações.

**3.4 PIBRAS Migration Studio** — módulo específico para migração e importação de bases externas.
Aceita CSV, Excel, XML, APIs, feeds de portais, dumps de bancos legados, exportações de CRMs e de
sistemas nacionais. Funções: upload; leitura da estrutura; detecção automática de colunas; sugestão de
mapeamento; mapeamento manual; normalização; deduplicação; relatório de qualidade; revisão humana;
importação final.

**3.5 PIBRAS Connect** — camada de conectores (Kenlo, Vista, Jetimob, Imobzi, Tecimob, Órulo, ZAP,
Viva Real, OLX, Chaves na Mão, RD Station, TwentyCRM, HubSpot, Pipedrive, sites próprios, ERPs,
planilhas, XMLs, portais regionais). Cada conector segue um contrato comum:

```txt
fetch · map · validate · normalize · upsert · sync · report
```

**3.6 PIBRAS API** — API pública e documentada: REST; OpenAPI/Swagger; Postman Collection; SDK
TypeScript; SDK Python; webhooks; autenticação; rate limits; logs; documentação de exemplos.

**3.7 PIBRAS Match** — motor opcional de recomendação entre cliente e imóvel (Property Matching
Engine). Cruza perfil do cliente, histórico comercial, preferências, orçamento, bairros, estilo de
vida, momento de compra, imóveis disponíveis e off-market, características subjetivas, objeções
anteriores e timing comercial.

**3.8 PIBRAS Intelligence** — camada opcional de IA, enriquecimento, auditoria e análise: resumo de
imóveis e clientes; enriquecimento; normalização com IA; análise de duplicidade; recomendação de
abordagem comercial; identificação de oportunidades; estoque parado; reativação de leads; briefings;
scoring de liquidez e match.

**3.9 PIBRAS Reference Stack** — stack recomendada (não obrigatória):

```txt
PIBRAS Core · Directus · Postgres · Windmill · TwentyCRM · Hermes Agent · Metabase
```

## 4. Hermes Agent + TwentyCRM

**4.1 TwentyCRM** — sistema de registro comercial: contatos, empresas, oportunidades, tarefas, notas,
pipeline, brokers, histórico, atividades, relacionamento, follow-ups. No contexto da MBRAS, organiza a
operação comercial, mas não deve necessariamente ser o inventário mestre de imóveis.

**4.2 Hermes Agent** — operador inteligente ao redor do CRM: limpar duplicados; enriquecer leads;
criar follow-ups; resumir histórico; detectar oportunidades paradas; preparar briefings; monitorar
inbox; interpretar notas; sugerir próximos passos; classificar leads; recomendar imóveis; gerar
relatórios.

**4.3 Governança** — Hermes não altera tudo livremente: (1) lê e analisa; (2) propõe atualizações; (3)
baixo risco pode ser automático; (4) sensível exige aprovação humana. *Baixo risco:* criar tarefas,
adicionar notas, marcar lead como pendente de revisão, atualizar campo de última análise, sugerir
ação. *Alto risco:* trocar broker, marcar oportunidade como perdida, alterar valor, deletar/mesclar
contatos, alterar classificação sensível, enviar mensagem ao cliente.

> Twenty armazena a verdade. Hermes melhora a verdade. Brokers validam a verdade.

## 5. Windmill ou n8n

**n8n** — automações rápidas, conectores prontos, times mistos, marketing, operações, prototipagem,
fluxos visuais, integrações simples. **Windmill** — arquitetura técnica, workflows críticos, scripts
versionados, APIs internas, jobs agendados, automações robustas, regras complexas, lógica em código,
integração com IA, governança.

Conclusão: para operação simples, n8n pode bastar; para a MBRAS e o PIBRAS, Windmill é mais adequado
como backbone técnico (deduplicação, enriquecimento, classificação, tarefas, alertas, aprovação,
webhooks, integrações, scripts, rotinas diárias, endpoints internos). Parte da stack recomendada, mas
não obrigatório.

## 6. Postgres, Directus e Metabase

- **Postgres** — banco principal, histórico e auditoria: imóveis, listings, unidades, empreendimentos,
  proprietários, mídias, documentos, regras de exposição, importações, logs, histórico de preço/status,
  decisões da IA, scores, eventos comerciais.
- **Directus** — interface administrativa e API automática (REST/GraphQL) sobre o banco; pode funcionar
  como Property Inventory Hub inicial e backoffice. Parte da stack de referência; PIBRAS não deve
  depender dele.
- **Metabase** — dashboards gerenciais: leads por origem, tempo de resposta por broker, oportunidades
  sem follow-up, taxa de visita/proposta, conversão por bairro, demanda por tipologia, estoque parado,
  motivos de perda, pipeline por ticket, reativação.

## 7. Property Inventory Hub

Antes do nome PIBRAS, o conceito foi discutido como Property Inventory Hub: centralizar inventário,
mídias, documentos, regras de exposição e inteligência. Controla status comercial, exposição
pública/privada/off-market, proprietário, captação, broker responsável, preço pedido, preço mínimo
recomendado, liquidez, mídia aprovada, material jurídico, bairros, atributos subjetivos, privacidade,
arquitetura, vista, raridade, compatibilidade com clientes.

> O Property Inventory Hub evolui para PIBRAS. PIBRAS é o nome do projeto maior; o Property Inventory
> Hub é uma das funções centrais do PIBRAS.

## 8. Property Matching Engine

Motor de recomendação que cruza o perfil de cada cliente com o inventário: **cliente certo × imóvel
certo × momento certo × abordagem certa.**

Um filtro comum responde "mostre coberturas no Itaim acima de 400 m²". Um Matching Engine responde:

```txt
Este cliente valoriza privacidade, arquitetura contemporânea e localização próxima ao Parque do Povo.
Estes três imóveis têm maior chance de avançar para visita. O primeiro é o match racional, o segundo é
o aspiracional, o terceiro é a alternativa estratégica.
```

**Dados do cliente:** bairro desejado, orçamento, tipo, metragem, suítes, estilo de vida, urgência,
perfil familiar, preferências (prédio novo/casa/cobertura/condomínio/vista/privacidade/segurança/
arquitetura/lazer), histórico de visitas, imóveis recusados, objeções, origem do lead, temperatura.

**Dados do imóvel:** código, bairro, valor, área, tipologia, suítes, vagas, status, pronto/lançamento/
off-market, arquitetura, privacidade, vista, liquidez, exclusividade, perfil do prédio/condomínio,
proximidades (escolas, clubes, restaurantes, parques), potencial de valorização, silêncio, luz, jardim,
raridade.

**Tipos de match:** (1) direto — bate objetivamente; (2) aspiracional — acima do orçamento/escopo, mas
com alto potencial de encantamento; (3) estratégico — alternativa que resolve a intenção real mesmo com
diferenças.

```txt
Cliente A × Heritage by Pininfarina
Bairro 95% · Metragem 90% · Tipologia 100% · Privacidade 85% · Arquitetura 95% · Orçamento 75% ·
Urgência 80% · Histórico de interesse 90%  →  Score final 88/100
```

Para a MBRAS é estratégico porque o altíssimo padrão não funciona só por busca e filtro: depende de
interpretação, curadoria, timing, relacionamento, discrição, memória comercial, estoque off-market,
leitura subjetiva do cliente e inteligência do broker.

## 9. Repositório de Property Matching Engine

Busca nos repos GitHub conectados não encontrou repositório específico de matching. Repos MBRAS
encontrados: `mbras-web-teste`, `mbras-dev-playbook`, `mbras-ads`, `mbras-lux-report`,
`mbras-assignture`, `mbras-webapp-v3`. O mais próximo seria `mbras-webapp-v3` (plataforma imobiliária em
Next.js), mas estava arquivado e sem sinais claros de matching. **Conclusão:** o Matching Engine ainda
precisa ser criado. Nomes possíveis: `mbras-property-matching-engine`, `mbras-commercial-intelligence`,
`pibras-match`. Se o projeto se tornar PIBRAS, o nome mais coerente é **`pibras-match`**.

## 10. Ferramentas de mercado semelhantes

**CRMs imobiliários com automação/IA** (BoomTown, Lofty/Chime, Follow Up Boss, RealOffice360) — bons
para CRM, lead management, nurturing, pipeline, automações, sites, analytics; mas não resolvem
plenamente curadoria de altíssimo padrão, off-market, regras de exposição sensíveis, matching
subjetivo, padrão brasileiro de interoperabilidade, migração universal e dados canônicos.

**Plataformas de matching/recomendação** (RealScout, ListAssist, Anyone.com, HomeLight, Nestopa) — se
aproximam de busca inteligente/matching, mas geralmente voltadas a mercados com MLS/IDX mais
estruturado ou a marketplaces. **Conclusão:** existe coisa parecida, mas não foi identificada solução
que substitua bem um Matching Engine proprietário adaptado ao Brasil e ao altíssimo padrão.

## 11. Sistemas nacionais e APIs

Observação: no Brasil muitos sistemas falam em integração, mas nem sempre oferecem API pública bem
documentada — às vezes é API privada, XML, feed para portais, webhook sob contrato ou integração via
parceiro.

- **Sistemas imobiliários:** Kenlo, Vista Software, Jetimob, Imobzi, Tecimob, Órulo, Universal
  Software, sistemas próprios de incorporadoras, CRMs legados, ERPs imobiliários.
- **Portais:** ZAP, Viva Real, OLX Imóveis, Chaves na Mão, Casa Mineira, WImoveis, Imovelweb, regionais.
- **Dados/enriquecimento:** DataZAP, Geoimóvel, Loft Dados, CNPJ APIs, Google Maps/Places, IBGE,
  ViaCEP, bases de endereço e de mercado.
- **Documentos/contratos:** Clicksign, ZapSign, DocuSign, Google Drive, SharePoint.
- **Comunicação:** WhatsApp Business API, Zenvia, Take Blip, Weni, 360dialog, Gmail, Google Calendar.
- **Financeiro/ERP:** Asaas, Conta Azul, Omie, Nibo.
- **Automação/integração:** Pluga, Windmill, n8n, APIs próprias, webhooks, filas.

## 12. O que pedir nas API docs dos fornecedores

```txt
1. Documentação REST API ou GraphQL          11. Endpoint de visitas
2. Swagger/OpenAPI ou Postman Collection      12. Endpoint de propostas
3. Autenticação: API key, OAuth2, JWT         13. Endpoint de contratos
4. Rate limits                                14. Endpoint de status de publicação
5. Webhooks disponíveis                       15. Exportação XML/feed para portais
6. Endpoint de imóveis                        16. Permissões por usuário
7. Endpoint de fotos, vídeos e plantas        17. Logs/auditoria
8. Endpoint de proprietários                  18. LGPD e política de retenção
9. Endpoint de leads                          19. Ambientes sandbox/homologação
10. Endpoint de corretores                    20. Custo adicional de API
```

## 13. PIBRAS como arquitetura de ecossistema

Visão final: *Ecosystem Architecture* e *Master Data Management* para o setor imobiliário brasileiro. A
maioria dos sistemas é acoplada ("meu site fala com meu banco"). O PIBRAS propõe outro modelo:
"sistemas diferentes falam uma linguagem comum."

**Posição estratégica:** não apresentar como "o novo sistema imobiliário da MBRAS", e sim como "um
padrão aberto para o mercado imobiliário brasileiro" — isso reduz resistência e convida o ecossistema.

**Papel da MBRAS:** idealizadora, primeira apoiadora, primeira usuária, case inicial, curadora da
visão, patrocinadora institucional, convidadora de parceiros. A MBRAS não deve parecer dona fechada do
ecossistema.

> O PIBRAS nasce a partir de uma necessidade real da MBRAS, mas com uma ambição maior: criar uma
> infraestrutura aberta para o mercado imobiliário brasileiro.

## 14. Conceito de modelo canônico

Para conversar com todos os sistemas, o PIBRAS precisa de um modelo de dados canônico:

```txt
Sistema externo: valor / preco_venda / preço / listingPrice / sale_value
Modelo PIBRAS:   property.pricing.asking_price_brl
```

Não importa como cada sistema chama o campo; dentro do PIBRAS o campo tem um nome único. Isso evita que
o código vire uma sequência de condicionais frágeis.

**Normalização:**

```txt
Jd. Europa → Jardim Europa
V. Nova Conceição → Vila Nova Conceição
R$ 12.000.000,00 → 12000000
740m2 → 740
sim/não → true/false
```

## 15. Separação entre Property e Listing

Decisão arquitetural mais importante. **Property** é o imóvel físico (ex.: cobertura duplex no Itaim,
570 m², 4 suítes, 6 vagas, Rua Leopoldo Couto de Magalhães Júnior). **Listing** é a forma como o imóvel
é exposto em um canal: público no site; privado para brokers; off-market; portais; internacional; PDF;
campanha; sem preço; sem endereço; sem fotos de fachada.

No altíssimo padrão, um imóvel não pode ser tratado apenas como anúncio: o mesmo ativo pode ter
narrativas, preços exibidos, mídias, regras de exposição, níveis de confidencialidade, canais e
públicos diferentes.

## 16. Entidades principais do PIBRAS

**Estratégicas:**

```txt
Property · Listing · Building · Unit · Owner · Broker · MediaAsset · Document ·
PublicationChannel · ExposureRule · PriceHistory · StatusHistory · LeadInterest ·
Visit · Offer · ComparableProperty · PropertyIntelligence · ImportSource · ImportBatch · ImportMapping
```

**MVP:**

```txt
Property · Listing · Building · Unit · Owner · MediaAsset · ExposureRule ·
ImportSource · ImportBatch · ImportMapping
```

Essas entidades já permitem: importar estoque; separar imóvel físico de anúncio; controlar mídia;
controlar confidencialidade; mapear campos externos; resolver duplicatas; preparar distribuição para
site, CRM e portais; abrir caminho para o matching engine.

## 17. Property

Entidade central — o imóvel físico/ativo. Campos conceituais: `id`, `mb_code`, `external_ids`, `type`,
`subtype`, `status`, `confidentiality_level`, `transaction_type`, `address`, `areas`, `features`,
`pricing`, `governance`.

```json
{
  "id": "uuid",
  "mb_code": "MB18495",
  "external_ids": [ { "source": "kenlo", "external_id": "123456" } ],
  "type": "apartment",
  "subtype": "duplex_penthouse",
  "status": "active",
  "confidentiality_level": "private",
  "transaction_type": "sale",
  "address": {
    "country": "BR", "state": "SP", "city": "São Paulo",
    "neighborhood": "Itaim Bibi",
    "street": "Rua Leopoldo Couto de Magalhães Júnior",
    "number": null, "complement": null, "postal_code": null,
    "latitude": null, "longitude": null,
    "display_address": "Rua Leopoldo Couto de Magalhães Júnior, Itaim Bibi"
  },
  "areas": { "private_area_m2": 570, "built_area_m2": null, "land_area_m2": null, "total_area_m2": null },
  "features": {
    "bedrooms": null, "suites": 4, "bathrooms": null, "parking_spaces": 6, "floor": null,
    "has_pool": true, "has_garden": false, "has_view": true, "furnished": true
  },
  "pricing": {
    "asking_price_brl": null, "minimum_price_brl": null,
    "condominium_fee_brl": null, "iptu_brl": null, "price_visibility": "on_request"
  },
  "governance": {
    "source_of_truth": "mbras", "created_by": "user_id", "updated_by": "user_id",
    "created_at": "2026-06-18T00:00:00Z", "updated_at": "2026-06-18T00:00:00Z",
    "requires_review": false
  }
}
```

## 18. Listing

Exposição de um imóvel em determinado canal. Campos: `id`, `property_id`, `channel`, `listing_type`,
`status`, `title`, `description`, `price_display`, `address_display_mode`, `media_policy`, `visibility`.

```json
{
  "id": "uuid",
  "property_id": "uuid",
  "channel": "mbras_website",
  "listing_type": "public",
  "status": "published",
  "title": "Cobertura duplex mobiliada no Itaim Bibi",
  "description": "Texto público aprovado para exposição.",
  "price_display": "Sob consulta",
  "address_display_mode": "neighborhood_only",
  "media_policy": { "allow_facade": false, "allow_street_view": false, "allow_floor_plan": true, "allowed_media_ids": [] },
  "visibility": { "public": true, "brokers_only": false, "directors_only": false, "qualified_clients_only": false }
}
```

## 19. Building, Condominium e Unit

**Building / Condominium** — o empreendimento, prédio ou condomínio: nome, endereço, bairro, cidade,
incorporadora, construtora, arquiteto, ano de entrega, amenities, segurança, lazer, mídia compartilhada,
regras do condomínio, perfil do empreendimento.

**Unit** — uma unidade dentro de um Building (ex.: Edifício X, unidade 2101, 570 m², 4 suítes, 6 vagas).

**Herança de mídia** — para lançamentos/empreendimentos, o Building tem sua própria galeria e as Units
herdam automaticamente fotos da fachada, áreas comuns, piscina, academia, lobby, jardins, imagens do
empreendimento e plantas gerais. Isso evita duplicação de mídia.

## 20. Owner

Proprietário ou responsável pelo ativo. Campos: `id`, `name`, `type`, `cpf_cnpj`, `contacts`,
`preferred_contact_method`, `privacy_level`, `documents`, `ownership_percentage`, `relationship_owner`,
`notes`. Pontos sensíveis: LGPD, confidencialidade, acesso restrito, logs, field-level security,
aprovação para exposição.

## 21. MediaAsset

Fotos, vídeos, plantas, tours e materiais. Campos: `id`, `property_id`, `building_id`, `unit_id`,
`type`, `url`, `storage_path`, `title`, `description`, `credit`, `copyright_status`, `approval_status`,
`visibility_level`, `allowed_channels`, `is_public`, `is_internal`, `is_confidential`, `created_at`,
`updated_at`. Tipos: foto, vídeo, drone, planta, tour virtual, PDF, imagem de campanha, render,
documento visual, fachada, área comum, interior, localização.

## 22. Document

Documentos jurídicos, comerciais e administrativos: matrícula, IPTU, condomínio, autorização de venda,
autorização de divulgação, NDA, proposta, contrato, memorial descritivo, planta técnica, documentos do
proprietário. Campos: `id`, `property_id`, `owner_id`, `type`, `file_url`, `status`, `visibility_level`,
`requires_signature`, `signature_provider`, `expiration_date`, `created_at`, `updated_at`.

## 23. ExposureRule

Entidade crítica para altíssimo padrão — define o que pode ou não ser exibido. Campos: `id`,
`property_id`, `listing_id`, `confidentiality_level`, `can_publish_on_website`,
`can_publish_on_portals`, `can_publish_on_social`, `can_send_by_whatsapp`, `can_show_price`,
`can_show_address`, `can_show_street`, `can_show_number`, `can_show_facade`, `can_show_floor_plan`,
`can_show_owner`, `brokers_only`, `directors_only`, `qualified_clients_only`, `requires_owner_approval`,
`requires_director_approval`.

```txt
Se status = confidencial:
- ocultar número do imóvel; ocultar fachada; ocultar proprietário;
- exibir apenas bairro; liberar detalhes apenas para diretoria ou broker autorizado.
```

## 24. Field-level security

Segurança por imóvel não basta; é necessário controlar acesso por campo.

```txt
address.street: visível para brokers autorizados
address.number: visível apenas para diretoria
owner.name: visível apenas para diretoria e broker responsável
pricing.minimum_price_brl: visível apenas para diretoria
documents: visível conforme permissão
```

A API responde dados diferentes para usuários diferentes:

```txt
Público:  Bairro: Itaim Bibi · Endereço: null · Preço: Sob consulta
Broker:   Rua: Rua Leopoldo Couto de Magalhães Júnior · Número: null · Preço: Sob consulta
Diretor:  Rua + Número: 1201 · Preço mínimo: disponível · Proprietário: disponível
```

## 25. ImportSource, ImportBatch e ImportMapping

Sustentam o Migration Studio.

**ImportSource** — origem dos dados (Kenlo, Vista, Jetimob, planilha, XML, site antigo, CRM legado,
sistema próprio). Campos: `id`, `name`, `type`, `auth_type`, `base_url`, `status`, `last_sync_at`,
`created_at`, `updated_at`.

**ImportBatch** — uma importação específica. Campos: `id`, `source_id`, `file_name`, `status`,
`total_rows`, `valid_rows`, `invalid_rows`, `duplicates_found`, `conflicts_found`, `started_at`,
`finished_at`, `report_url`, `created_by`.

**ImportMapping** — o de/para entre campos externos e campos PIBRAS:

```txt
"Valor"     → property.pricing.asking_price_brl
"Bairro"    → property.address.neighborhood
"Dorms"     → property.features.bedrooms
"CodImovel" → property.external_ids.external_id
```

Campos: `id`, `source_id`, `external_field`, `pibras_field`, `transform_rule`, `required`,
`created_at`, `updated_at`.

## 26. Migration Studio

```txt
1. Usuário escolhe origem            8. Sistema detecta duplicatas
2. Upload ou conecta API             9. Sistema identifica conflitos
3. Sistema lê estrutura             10. Sistema gera relatório
4. Sistema sugere mapeamento        11. Usuário aprova
5. Usuário revisa de/para           12. Sistema importa
6. Sistema valida dados             13. Sistema registra auditoria
7. Sistema normaliza formatos
```

**Relatório de importação:** `Importar 1.248 · Atualizar 438 · Ignorar 92 duplicados · Revisar 37
conflitos`.

**Quality score:** `Completeness score: 84% — faltando: planta, vídeo, regra de exposição, perfil ideal
de comprador, valor de condomínio`.

## 27. Deduplicação e Entity Resolution

Identificar que "R. Oscar Freire, 1000", "Rua Oscar Freire 1000" e "Oscar Freire, mil" são o mesmo
lugar.

**Critérios:** endereço, bairro, cidade, condomínio, metragem, preço, fotos parecidas, proprietário,
código antigo, coordenadas, matrícula, andar, unidade, telefone do proprietário, descrição similar.

**Normalização de endereço:** Google Maps API, bases dos Correios, ViaCEP, geocoding, regras próprias,
tabelas de bairros.

**IA e embeddings:** embeddings de descrições; similaridade de fotos; comparação de plantas; análise de
imagem; agrupamento por atributos; score de confiança. A decisão final pode ir para revisão humana.

## 28. Governança e conflitos

```txt
Kenlo: ativo · Planilha: vendido · Broker: off-market · Site: publicado
```

**Regra de prioridade:**

```txt
1. Atualização manual aprovada pela diretoria   4. Sistema externo principal
2. Sistema interno MBRAS                         5. Feed XML
3. TwentyCRM                                      6. Planilha importada
```

**Regra de ouro:** nunca deixar integração externa destruir dado proprietário. Dados externos entram
como sugestão, atualização pendente, conflito, enriquecimento ou nova versão. Dados sensíveis exigem
aprovação.

## 29. Versionamento e auditoria

Eventos auditáveis: preço, status, fotos, descrição, canal de publicação, broker responsável,
proprietário, regra de exposição, documento adicionado, importação realizada, conflito resolvido.

```txt
MB18495 · Preço anterior R$ 18.000.000 → novo R$ 17.500.000 · por Broker X · origem Kenlo sync · 18/06/2026
```

## 30. Arquitetura orientada a eventos

Para escala, o PIBRAS deve ser event-driven: quando um XML com milhares de imóveis entra, enviar
eventos para uma fila (Kafka, RabbitMQ, AWS SQS, Google Pub/Sub, Redis Queue, Temporal). Benefícios:
evita derrubar servidor, permite retry, desacopla etapas, paraleliza, melhora resiliência, facilita
auditoria, suporta integrações instáveis, permite pausar/retomar.

```txt
ImportBatchCreated · PropertyRowParsed · PropertyMapped · PropertyValidated ·
DuplicateCandidateFound · PropertyApproved · PropertyUpserted · ListingPublished · MediaProcessed · SyncFailed
```

## 31. CQRS e camada de leitura

A escrita é pesada (valida, deduplica, audita, versiona, resolve conflito, aplica segurança,
normaliza); a leitura precisa ser rápida. Por isso, CQRS: escrita em Postgres; índice de leitura em
Elasticsearch, OpenSearch, Meilisearch, Typesense ou Redis. Permite buscas como "imóveis com varanda,
perto do Ibirapuera, entre 10 e 15 milhões". A Distribution Layer consulta o índice para site, CRM,
portais, PDFs, campanhas e apps.

## 32. REST, GraphQL e Webhooks

**REST** — integrações externas, operações simples, endpoints claros, Postman, OpenAPI:

```txt
GET /properties · GET /properties/{id} · POST /properties · PATCH /properties/{id}
```

**GraphQL** — consumo interno: o CRM pede só `id`, `preço`, `1 foto`; o site pede fotos, descrição,
amenities, corretor; o app interno pede dados sensíveis conforme permissão. Cada canal pede exatamente
os campos necessários.

**Webhooks:**

```txt
property.created · property.updated · property.status_changed · property.price_changed ·
listing.published · listing.unpublished · media.approved · import.completed · duplicate.found
```

## 33. Architecture overview

```txt
Sistemas externos (Kenlo, Vista, Jetimob, Imobzi, Tecimob, CRMs, portais, XMLs, planilhas)
   ↓ PIBRAS Connect (APIs, webhooks, XML, CSV, Excel, importadores manuais)
   ↓ Mapping Layer (tradução dos campos externos para o modelo canônico PIBRAS)
   ↓ Validation Layer (validação, normalização, deduplicação e conflitos)
   ↓ PIBRAS Core (inventário, listings, mídia, documentos, regras de exposição, logs e auditoria)
   ↓ PIBRAS Intelligence (Hermes Agent, IA, matching, scoring, enriquecimento, curadoria)
   ↓ Distribution Layer (TwentyCRM, site, portais, brokers, PDFs, campanhas, dashboards)
```

## 34. Stack recomendada

```txt
PIBRAS Standard · PIBRAS Core · PIBRAS Studio · Directus · Postgres · Windmill · TwentyCRM · Hermes Agent · Metabase
```

Funções: PIBRAS Standard (padrão aberto) · PIBRAS Core (implementação oficial) · PIBRAS Studio (gestão,
importação, validação) · Directus (backoffice e API rápida) · Postgres (banco, histórico, auditoria) ·
Windmill (workflows, jobs, scripts, APIs internas, automações) · TwentyCRM (CRM comercial) · Hermes
Agent (camada inteligente) · Metabase (BI e dashboards).

**Importante:** recomendação, não obrigação. Quem discordar pode usar apenas PIBRAS Standard, API,
Connectors, Migration Studio, schemas e SDK.

## 35. Como terceiros podem usar o PIBRAS

- **Imobiliária que usa Kenlo:** Kenlo atual → PIBRAS Connector para importar → PIBRAS Standard para
  normalizar → Migration Studio para limpar duplicidades → PIBRAS API para distribuir ao site próprio.
- **Incorporadora com sistema próprio:** sistema interno → PIBRAS Standard → PIBRAS OpenAPI → conector
  customizado → distribuição para parceiros e portais.
- **MBRAS com stack completa:** PIBRAS Core · Directus · Postgres · Windmill · TwentyCRM · Hermes Agent ·
  Metabase · PIBRAS Match.
- **Desenvolvedor independente:** usa `pibras-standard` → cria um conector → contribui com schema → cria
  integração com portal → cria plugin para CRM → usa SDK TypeScript ou Python.

## 36. Repositórios sugeridos

**Separação completa:**

```txt
pibras-standard      Schemas, especificação, documentação e exemplos
pibras-core          API principal e implementação de referência
pibras-studio        Interface de importação, migração e governança
pibras-connectors    Conectores oficiais e comunitários
pibras-sdk-js        SDK TypeScript/JavaScript
pibras-sdk-python    SDK Python
pibras-examples      Exemplos de integração com CRM, site, portal e planilha
pibras-match         Motor opcional de recomendação imóvel × cliente
pibras-docs          Documentação pública
```

**Início simplificado:** `pibras-standard · pibras-core · pibras-connectors`. Começar simples, mas já
com visão modular.

## 37. MVP recomendado

```txt
1. PIBRAS Standard v0.1        6. Deduplicação básica
2. JSON Schema das entidades   7. Quality score
3. OpenAPI inicial             8. API de properties e listings
4. Importador CSV/Excel/XML    9. Conector TwentyCRM ou exportação para CRM
5. Mapping visual simples     10. Documentação pública
```

**Entidades do MVP:** Property, Listing, Building, Unit, Owner, MediaAsset, ExposureRule, ImportSource,
ImportBatch, ImportMapping.

**Fluxo MVP:** subir planilha → mapear campos para o padrão PIBRAS → validar → identificar duplicatas →
criar properties → criar listings → aplicar regras de exposição → expor via API → enviar para site/CRM.

## 38. Roadmap sugerido

- **Fase 1 — Fundacional:** definir o PIBRAS Standard v0.1; JSON Schemas; OpenAPI; documentação;
  estrutura de repositórios; licença open-source; manifesto técnico.
- **Fase 2 — Core e importação:** PIBRAS Core; banco Postgres; endpoints básicos; importador
  CSV/Excel/XML; mapping visual; relatório de qualidade; deduplicação básica.
- **Fase 3 — Integrações:** conector TwentyCRM; conector site; conector XML genérico; conector Kenlo ou
  Vista; conector portal; webhooks.
- **Fase 4 — Inteligência:** PIBRAS Intelligence; Hermes Agent; summaries; enrichments; deduplicação
  semântica; scores de qualidade, liquidez e match.
- **Fase 5 — PIBRAS Match:** motor de recomendação; cliente × imóvel; lead × estoque; reativação;
  briefing de broker; matching off-market.
- **Fase 6 — Ecossistema:** convite a desenvolvedores e parceiros; documentação pública; SDKs; plugins;
  exemplos; comunidade; governança open-source.

## 39. Mensagem para desenvolvedores

> O PIBRAS não quer substituir todos os sistemas imobiliários. Ele quer criar uma linguagem comum para
> que eles consigam conversar. Se você desenvolve para imobiliárias, incorporadoras, portais, CRMs ou
> ERPs, pode usar o PIBRAS como padrão de dados, camada de importação, API, conector ou referência para
> interoperabilidade. A proposta é simples: menos retrabalho, menos duplicidade, migrações mais seguras,
> dados mais consistentes e uma base preparada para IA.

## 40. Mensagem para parceiros do segmento

> O mercado imobiliário brasileiro ainda opera com dados fragmentados, cadastros duplicados e
> integrações frágeis. O PIBRAS nasce para criar uma camada aberta de organização e interoperabilidade
> para imóveis, anúncios, mídias, documentos, proprietários e canais de publicação. A iniciativa permite
> que imobiliárias, incorporadoras, portais e fornecedores de tecnologia conversem melhor, migrem dados
> com mais segurança e preparem seus inventários para uma nova etapa de inteligência comercial.

## 41. Texto-base institucional

> O PIBRAS, Portfólio Imobiliário do Brasil, nasce como uma iniciativa aberta para organizar,
> padronizar e integrar dados imobiliários no Brasil.
>
> O mercado imobiliário brasileiro ainda opera com bases fragmentadas, cadastros duplicados, integrações
> frágeis, migrações difíceis e pouca padronização entre sistemas, portais, CRMs, sites e ERPs. Cada
> plataforma fala sua própria linguagem. O resultado é perda de dados, retrabalho, baixa governança e
> dificuldade para aplicar inteligência artificial com segurança.
>
> O PIBRAS propõe uma camada comum para esse ecossistema. Mais do que um software, o PIBRAS é um padrão
> aberto de dados imobiliários. Ele define como imóveis, anúncios, unidades, empreendimentos,
> proprietários, mídias, documentos, regras de exposição, status, preços e canais devem ser
> estruturados, importados, validados e distribuídos.
>
> A iniciativa parte de um princípio simples: o imóvel físico não é a mesma coisa que o anúncio. Um
> mesmo ativo pode ter diferentes formas de exposição, diferentes níveis de confidencialidade,
> diferentes canais de publicação e diferentes narrativas comerciais. Essa separação é essencial para um
> mercado mais profissional, seguro e interoperável.
>
> O PIBRAS poderá ser usado de diferentes formas. Quem quiser começar do zero poderá adotar a stack de
> referência. Quem já utiliza CRM, ERP, portal, site próprio ou sistema imobiliário poderá usar apenas o
> padrão, a API, os conectores ou o Migration Studio. A proposta não é substituir todos os sistemas
> existentes, mas permitir que eles conversem melhor.
>
> A MBRAS inicia o projeto como idealizadora e primeira apoiadora, convidando desenvolvedores,
> imobiliárias, incorporadoras, portais, fornecedores de tecnologia e parceiros do segmento a participar
> da construção de um padrão mais aberto, confiável e preparado para o futuro.
>
> O objetivo do PIBRAS é criar uma infraestrutura comum para o portfólio imobiliário brasileiro:
> importável, auditável, extensível, seguro e pronto para inteligência artificial.

## 42. Manifesto curto

> O mercado imobiliário brasileiro precisa de uma linguagem comum. Imóveis, anúncios, mídias,
> documentos, proprietários, portais, CRMs e sistemas ainda vivem em bases fragmentadas, com integrações
> frágeis e migrações difíceis. O PIBRAS nasce para mudar isso. Não como mais um sistema fechado, mas
> como um padrão aberto para organizar, migrar, integrar e distribuir dados imobiliários. Um imóvel não
> é apenas um anúncio. Um portfólio não é apenas uma lista. Dados imobiliários exigem contexto,
> governança, segurança, histórico e inteligência. O PIBRAS é o Portfólio Imobiliário do Brasil. Uma
> infraestrutura aberta para um mercado mais integrado, profissional e preparado para IA.

## 43. Princípios do PIBRAS

```txt
1. Aberto por padrão                         11. Preparado para IA
2. Independente de fornecedor                12. Seguro por design
3. API-first                                 13. Field-level security
4. Import-first                              14. Separação entre Property e Listing
5. Migration-ready                           15. Interoperabilidade antes de lock-in
6. Connector-based                           16. Stack recomendada, mas opcional
7. Data-model driven                         17. Dados externos não sobrescrevem proprietários sem governança
8. Auditável                                 18. Humano aprova mudanças sensíveis
9. Multi-origem                              19. O padrão deve ser maior do que a ferramenta
10. Multi-canal                              20. O ecossistema deve ser maior do que a MBRAS
```

## 44. O que não fazer

```txt
- Não posicionar como novo CRM da MBRAS.
- Não posicionar como substituto obrigatório de Kenlo, Vista, Jetimob ou outros.
- Não criar dependência obrigatória de Directus, TwentyCRM ou Windmill.
- Não misturar imóvel físico com anúncio.
- Não deixar integrações externas sobrescreverem dados sensíveis automaticamente.
- Não construir primeiro conectores complexos antes do modelo canônico.
- Não começar com IA antes de limpar e padronizar dados.
- Não criar um monolito fechado.
- Não ignorar planilhas, CSVs e XMLs, porque serão essenciais para migração.
- Não tratar o mercado brasileiro como se fosse MLS americano.
```

## 45. Ordem recomendada de construção

```txt
1. Definir visão e manifesto              11. Criar deduplicação básica
2. Criar repositório pibras-standard      12. Criar relatório de qualidade
3. Escrever PIBRAS Standard v0.1          13. Criar PIBRAS Core
4. Definir entidades canônicas            14. Criar PIBRAS Studio MVP
5. Criar JSON Schemas                     15. Criar primeiro conector
6. Criar OpenAPI inicial                  16. Criar primeira integração CRM/site
7. Criar exemplos de payload              17. Publicar documentação
8. Criar importador CSV/Excel/XML         18. Convidar desenvolvedores e parceiros
9. Criar Mapping Layer                    19. Criar governança do projeto
10. Criar Validation Layer                20. Evoluir para IA e matching
```

## 46. Conclusão

O PIBRAS deve nascer como uma infraestrutura aberta para o mercado imobiliário brasileiro. A MBRAS pode
ser a idealizadora e primeira apoiadora, mas o projeto precisa ser maior do que uma necessidade interna.
A oportunidade está em criar: um padrão de dados; uma camada de interoperabilidade; uma ferramenta de
migração; uma API comum; conectores para sistemas existentes; uma base auditável; uma estrutura pronta
para IA; um ecossistema de desenvolvedores e parceiros.

A stack recomendada pode ser poderosa (`PIBRAS Core · Directus · Postgres · Windmill · TwentyCRM ·
Hermes Agent · Metabase`), mas a mensagem estratégica deve permanecer: **PIBRAS é o padrão. A stack é
apenas uma forma de implementar.** O objetivo final é criar o Portfólio Imobiliário do Brasil — uma
camada aberta, segura, extensível e preparada para o futuro dos dados imobiliários no país.
