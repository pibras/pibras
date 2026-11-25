# Verificação de privacidade: condições operacionais, fixtures e saídas por canal

## 1. Objetivo e escopo

Este documento liga cada condição operacional de [privacy-operations.md](privacy-operations.md)
à fixture sintética que a exemplifica, à verificação executável que a exercita e ao canal de
saída que ela protege. Ele responde a uma pergunta: **para cada controle de privacidade que o
PIBRAS alega, o que o repositório de fato executa e o que depende do operador?**

- A norma continua em `privacy-operations.md`. Este documento não cria requisitos.
- A verificação executável está em `tests/contracts/test_privacy_channels.py`. O teste
  `TestVerificationDocTraceability` falha se uma fixture citada aqui deixar de existir ou se uma
  fixture de privacidade deixar de ser citada.
- As verificações usam exemplos sintéticos. Diferenças e correções
  encontradas estão em [§6](#6-lacunas-conhecidas), com o responsável provável segundo
  `docs/plans/v0.2-prontidao-publica.md`.
- Todos os dados são sintéticos. O próprio teste varre `tests/golden/` e falha se algum valor
  tiver o formato e o dígito verificador de um CPF válido.

Para executar:

```bash
rtk uv run pytest tests/contracts/test_privacy_channels.py
```

## 2. Legenda de estado

| Estado | Significado |
|---|---|
| **Testado** | Há verificação executável neste repositório, com teste que falha quando a proteção é removida. |
| **Parcial** | Há verificação, mas ela cobre só parte da condição. A parte restante está em §6. |
| **Lacuna** | A condição é exigida pela norma e nenhum artefato executável a impõe. |
| **Operador** | Obrigação do operador. O repositório só pode carregar a referência (`*_ref`), nunca provar a execução. Ver §5. |

## 3. Matriz: condição, fixture, verificação, saída

Colunas de fonte referem-se às seções de `privacy-operations.md`. A coluna "Verificação" nomeia a
classe ou função de teste em `tests/contracts/test_privacy_channels.py`.

| ID | Condição operacional | Fonte | Fixture | Verificação | Saída protegida | Estado |
|---|---|---|---|---|---|---|
| C1 | Campo, ação ou papel não definido é negado (default-deny); campo sensível só é liberado por regra explícita. | §2.7, §5.1.2, §5.1.4 | `tests/golden/exposure-policy.default-deny.json` | `TestDefaultDenyPolicy`: decisões da fixture, par papel/ação que lê `owner.tax_id`, `address.number` nunca liberado, mutações de `default_decision`, regra de negação removida e privilégio ampliado. | Decisão de leitura e exportação por papel. | Testado (avaliador de referência Python). Ver GAP-05. |
| C2 | Política confidencial lista seus canais, não inclui canal público e exige aprovação para `export` e `send`. | §5.1.2, §5.1.6 | `tests/golden/exposure-policy.default-deny.json` | `test_public_channels_are_not_in_allowed_channels`, `test_export_and_send_require_approval`. | Canais `crm` e `off_market_pdf`; bloqueio de `website`, `portal`, `paid_ad`. | Parcial. O teste valida a política declarada, não a execução do filtro de canal. Ver GAP-05 e GAP-07. |
| C3 | Projeção pública respeita `price_display` e `address_display`: sem preço numérico fora de `visible`, sem rua e número em endereço aproximado ou oculto. | §3, §5.1.4 | `tests/golden/listing.public-masked.json` | `TestListingProjection`: fixture e quatro mutações que vazam preço, rua, número e bairro. | Listing em `website`, `portal`, `paid_ad`. | Testado |
| C4 | Feed de portal não carrega `Price` sem `PriceDisplay=visible`, nem elementos restritos. | §3 | `tests/golden/portal-feed.valid.xml` | `TestPortalFeed`: validador do feed, mutação com `Price`, XML malformado, ausência de tags restritas e de CPF. | Feed XML de portal. | Testado |
| C5 | A superfície pública de banco é minimizada: exige listing público explícito, reduz coordenadas, suprime endereço oculto e exclui `draft`, `off_market`, `archived`. | §3, §5.1.2 | (nenhuma; usa `db/schema.sql`) | `TestPublicSurfaceDdl`: gate do CI, ausência de colunas restritas, igualdade entre colunas da view e `PUBLIC_SURFACE` do exportador, quatro mutações no texto da view. | View `property_public`. | Parcial. É verificação estática do texto. O comportamento está em `tests/postgres/property_public.sql`. |
| C6 | A exportação schema.org nasce da superfície pública, com preço exato e coordenadas reduzidas. | §3 | `tests/golden/schema-org.property-public.json` | `TestSchemaOrgChannel`: caso do CI, preço sem ponto flutuante, ausência de chaves restritas, precisão das coordenadas. | JSON-LD `RealEstateListing`. | Testado |
| C7 | Campo restrito ou registro não publicável é rejeitado pelo exportador, um a um. | §3, §5.1.4 | `tests/golden/schema-org.leaked-restricted-fields.invalid.json`, `tests/golden/schema-org.status-draft.invalid.json`, `tests/golden/schema-org.status-off-market.invalid.json`, `tests/golden/schema-org.status-archived.invalid.json` | `test_exporter_rejects_each_restricted_field` (parametrizado sobre `FORBIDDEN_FIELDS`), campo fora da superfície, cada status não publicável. | JSON-LD. | Testado |
| C8 | Fonte externa de baixa confiança não sobrescreve PII do proprietário sem revisão. | §3, §6 | `tests/golden/pending-change.owner-pii-protected.json` | `TestOwnerPiiAndSyntheticData`: estado `pending_review`, classe `pii`, camada de confiança menor que a atual, valor atual redigido. | Importação e fusão de dados. | Parcial. A fixture declara o resultado esperado; o teste Python não executa o motor de ingestão. |
| C9 | Fixtures e material de teste usam dados sintéticos, nunca um CPF válido. | §3, §6 | todas as fixtures de `tests/golden/` | `test_no_golden_fixture_contains_a_valid_cpf` e o teste do verificador de CPF. | Repositório público. | Testado |
| C10 | Finalidade explícita, com dono, e base legal avaliada com salvaguardas e evidência. | §2.1, §4 | `tests/golden/processing-purpose.valid.json`, `tests/golden/legal-basis-assessment.valid.json` | Validação de schema; `test_legal_basis_and_purpose_are_explicit_and_owned`. | Registro de decisão. | Parcial. Prova a forma do registro, não que a base escolhida seja adequada. Ver §5. |
| C11 | O parceiro tem papel, contrato, instrumento de privacidade e contato de DSAR antes de qualquer fluxo. | §5 | `tests/golden/partner-relationship.active.json` | `test_partner_has_contract_dpa_and_dsar_contact_before_any_flow`; schema rejeita `dpa_ref` ausente. | Habilitação do spoke. | Parcial. Referências presentes, vigência real é do operador. |
| C12 | A allowlist é versionada, ativa, aprovada, não vazia e sem caminho restrito. | §5.1.2 | `tests/golden/field-allowlist.active.json` | `test_allowlist_is_active_versioned_approved_and_minimal`, `test_allowlist_contains_no_restricted_field_path`; schema rejeita lista vazia. | Transferência hub para spoke. | Testado |
| C13 | O ledger registra caminhos de campo e digest, nunca os valores; só compartilha o que a allowlist permite, na versão vigente. | §5.1.3 | `tests/golden/sharing-event.delivered.json` | `test_ledger_shares_only_allowlisted_fields_at_the_allowlist_version`, `test_ledger_records_field_paths_and_digest_not_values`; schema rejeita payload copiado e lista vazia. | Ledger de compartilhamento. | Parcial. Coerência por nome de campo e versão. Ver GAP-03. |
| C14 | A solicitação do titular é registrada com efeito concreto e propagada ao parceiro com evidência ordenada no tempo. | §5.1.5, §7 | `tests/golden/data-subject-request.valid.json`, `tests/golden/data-subject-request.deletion-fulfilled.json`, `tests/golden/dsar-propagation.fulfilled.json` | `TestDsarRetentionAndDecisions`: evidência e ordem dos carimbos, efeito da exclusão dentro do prazo. | Propagação de DSAR a parceiros. | Testado no contrato canônico. Ver GAP-01 e GAP-02. |
| C15 | A retenção liga base legal, finalidade, prazo e ação ao expirar. | §7 | `tests/golden/retention-policy.valid.json` | `test_retention_policy_is_bound_to_basis_purpose_and_an_action`. | Expurgo e anonimização. | Parcial. Ver GAP-06. |
| C16 | Decisão unicamente automatizada expõe canal de revisão e explicação. | §4 | `tests/golden/automated-decision.reviewable.json` | `test_sole_automated_decision_exposes_review_and_explanation`. | Decisão automatizada. | Parcial. Prova as referências, não a revisão efetiva. |
| C17 | A onda de legado é qualificada (origem, compatibilidade, supressão) antes da importação. | §6 | `tests/golden/legacy-import-qualification.approved.json` | `test_legacy_wave_is_qualified_before_import`. | Importação de legado. | Parcial. Ver §5. |

As fixtures de C10 a C17 também são validadas contra o JSON Schema por
`test_privacy_fixture_validates_against_its_schema`. Os testes Node em `tests/types/mbras.test.ts`
repetem essa validação com Zod para oito delas, e recusam payload copiado no ledger e allowlist
vazia.

## 4. Rastreio por canal

Para cada canal, o caminho da decisão até a saída e o que cada elo tem de verificação.

| Canal ou saída | Decisão | Projeção ou serialização | Barreira final | Verificação |
|---|---|---|---|---|
| `crm`, `off_market_pdf` (política confidencial) | `ExposurePolicy` com default-deny (C1, C2) | Campos por papel e ação | Aprovação para `export` e `send` | Avaliador de referência Python (C1). |
| `website`, `portal`, `paid_ad` | Política, nível de exposição e aprovação do proprietário | Mascaramento de preço e endereço (C3) | Listing público explícito (C5) | Fixture (C3). O avaliador TypeScript é exercitado em `tests/types/engine.test.ts` com política inline, não com esta fixture (GAP-05). |
| Feed XML de portal | `PriceDisplay` e `AddressDisplay` do listing | Elementos do feed (C4) | Validador do feed | `TestPortalFeed`. |
| JSON-LD schema.org | Superfície `property_public` | Exportador (C6) | Rejeição de campo restrito e de status não publicável (C7) | `TestSchemaOrgChannel`. |
| View `property_public` | Listing público, publicado, ativo e não expirado | Colunas minimizadas (C5) | Texto da view protegido por gate | `TestPublicSurfaceDdl`; comportamento em `tests/postgres/property_public.sql`. |
| Hub para spoke (Sync Service) | Finalidade e base (C10), parceiro (C11), allowlist (C12) | Campos permitidos | Ledger sem valores (C13) | Fixtures e schema; coerência por nome (GAP-03). |
| DSAR para parceiros | Pedido do titular (C14) | Propagação por parceiro | Evidência e prazo | Fixtures; evidência obrigatória no schema (GAP-01). |
| Importação (legado e fontes externas) | Qualificação (C17), PII protegida (C8) | Fila de revisão | Estado `pending_review` | Fixtures; sem execução do motor em Python. |

## 5. Controle testado e obrigação do operador

O plano exige distinguir os dois. A regra aqui: **se a prova depende de algo que acontece fora do
repositório, é obrigação do operador**, ainda que exista uma fixture com a referência.

| Obrigação do operador | Fonte | Por que não é verificável aqui | Evidência que o operador deve manter |
|---|---|---|---|
| Aviso de privacidade coerente com enriquecimento e compartilhamento | §8 | Texto publicado ao titular não existe no repositório. | Versão do aviso e data de publicação. |
| Contrato e instrumento de privacidade realmente vigentes e compatíveis com os papéis reais | §5 | A fixture só carrega `contract_ref` e `dpa_ref`; vigência e conteúdo não são lidos. | Contrato assinado e revisão de papéis. |
| Avaliação de legítimo interesse e RIPD quando aplicáveis | §4 | Não há fixture de teste de finalidade, necessidade e balanceamento; a avaliação de exemplo usa a base `contract`. | Documento da avaliação e decisão de elaborar RIPD. |
| Adequação da base legal ao caso concreto | §2, §4 | O schema valida a forma da avaliação, não o mérito. | Parecer do encarregado ou do jurídico. |
| Autenticação do titular e respeito aos prazos reais de DSAR | §7 | Prazos nas fixtures são exemplos. | Registro do pedido, da autenticação e da resposta. |
| Execução real de expurgo, anonimização efetiva e retenção em produção | §7 | A política de retenção declara a ação; nada a executa neste repositório. | Relatório de expurgo por política. |
| Logs, telemetria, tickets, screenshots e ambientes não produtivos sem PII | §3, §6 | Só os dados do repositório são varridos. | Varredura de logs e revisão de acessos. |
| Revisão humana efetivamente prestada em decisão automatizada | §4 | A fixture aponta `review_request_ref` e `explanation_ref`; não prova atendimento. | Registro das revisões e dos prazos. |
| Resposta a incidente e comunicação à ANPD e aos titulares | §7 | Procedimento organizacional. | Plano testado e histórico de simulações. |
| Transferência internacional avaliada | §5 | Nenhuma fixture a modela. | Avaliação por destinatário. |
| Proprietário do controle, revisão periódica e procedimento de revogação | §8 | Governança do operador. | Registro de responsáveis e calendário de revisão. |

Consequência para o gate de produção (§8 da norma): os itens "allowlists e default-deny
testados" e "sharing ledger sem PII desnecessária" têm cobertura aqui. Os demais itens exigem a
evidência da coluna da direita e não se concluem apenas com esta suíte.

## 6. Lacunas conhecidas

O registro abaixo distingue correções verificadas de lacunas pendentes.

| ID | Observação | Tipo | Responsável provável |
|---|---|---|---|
| GAP-01 | Resolvida na representação canônica. Propagação cumprida requer evidência não vazia. | Teste de rejeição no schema e matriz JSON/Zod | A04 |
| GAP-02 | Resolvida. Exclusão cumprida requer ação e IDs afetados. | Testes de rejeição no contrato e no PostgreSQL | A04, A05 |
| GAP-03 | As fixtures de privacidade não se encadeiam por identificador: `field-allowlist.active.json` tem `id` iniciado em `1111`, enquanto `sharing-event.delivered.json` aponta `field_allowlist_id` iniciado em `3333`; o mesmo ocorre entre parceiro e allowlist, e entre DSAR e propagação. Só a coerência por nome de campo e versão é testada. Rastrear uma decisão de ponta a ponta por ID exige fixtures encadeadas. | Observação | A03, A07 |
| GAP-04 | Nomes e enumerações divergem entre JSON Schema e DDL. `SharingEvent` usa `shared_fields`, `field_allowlist_id`, `processing_purpose_id` e status `authorized`; a tabela usa `field_paths`, `allowlist_version_id`, `purpose_id` e `allowed`. `DSARPropagation` usa `evidence_ref` e `data_subject_request_id`; a tabela usa `external_reference` e `request_id`, e aceita o status `not_applicable`, ausente do schema. Não há mapeamento testado entre as duas representações. | Observação, por leitura | A04, A05 |
| GAP-05 | O avaliador TypeScript exige evidência confiável da atribuição do corretor. Condições desconhecidas ou sem evidência negam a operação. A comparação exaustiva por campo entre avaliadores permanece aberta. | Testes de política e HTTP | A06 |
| GAP-06 | `processing-purpose.valid.json` tem `retention_policy_id: null`. O schema permite, embora a norma ligue retenção a finalidade (§7). | Observação | A07 |
| GAP-07 | Lista de canais vazia ou ausente bloqueia o canal no avaliador TypeScript. O curinga explícito continua permitido. | Testes Node do avaliador | A06 |

Fora do escopo desta suíte: mutações sistemáticas de regra (frente A08), contrato HTTP (A06) e
comportamento do banco em PostgreSQL (A05). As mutações presentes aqui são verificações locais de
que cada gate falha quando sua proteção é removida; não substituem o harness de mutação.
