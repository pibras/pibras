# Aceite de release: matriz e processo de decisão

Este documento define **como** uma decisão de publicação do PIBRAS é tomada e **quais evidências verificáveis** a sustentam. Ele não aprova nenhuma release. Todo estado abaixo é um ponto de partida a ser substituído por evidência do candidato integrado.

Fontes: [`docs/plans/v0.2-prontidao-publica.md`](plans/v0.2-prontidao-publica.md), [`docs/VERSIONING.md`](VERSIONING.md), [`governance/release-policy.yaml`](../governance/release-policy.yaml), [`schema/release-policy.schema.json`](../schema/release-policy.schema.json), [`docs/rfcs/accepted-001-v0.2-reconciliation.md`](rfcs/accepted-001-v0.2-reconciliation.md), `.github/workflows/ci.yml`.

## Aplicação ao candidato integrado

A matriz abaixo registra o levantamento inicial em `5411f62`. As marcações de ausência e as observações sobre o workflow descrevem aquele levantamento. Para avaliar o candidato atual, use o roteiro abaixo e registre o resultado fora da árvore versionada, vinculado ao SHA verificado.

| Critérios | Verificação do candidato |
|---|---|
| Segurança, governança, contratos, titularidade, HTTP, privacidade e DDL | Em clone limpo, executar os modos `conformance` e `contracts` de `scripts/qa/verify.sh`. Registrar o SHA, resultados das duas auditorias, contagens, linhas de paridade, versão do Postgres e mutações detectadas. |
| Interoperabilidade e integridade | Construir dois ZIPs pelo procedimento em [PACKAGE.md](PACKAGE.md), comparar os bytes, extrair em diretório independente e executar o consumidor distribuído. Conferir que a alteração de um byte é rejeitada. |
| Promoção | Associar execução da CI e digest ao mesmo SHA. Encaminhar a divergência de magnitude monetária entre JSON Schema e Zod à RFC de Money/Settlement, registrar a decisão normativa e obter autorização de assinatura e promoção antes da publicação. |

## 1. Regras de leitura

1. **Nenhuma aprovação é presumida.** Um critério só é `Verde` quando existe um registro de evidência (seção 6) com SHA, comando, código de saída, data e executor. Texto de plano, RFC ou changelog não substitui execução.
2. **Aprovações externas não são geradas por automação.** Identidade, RFC, licença, assinatura e promoção final dependem de mantenedor. A automação só confere que o registro existe e é válido.
3. **Números do plano são referência inicial.** Os 21 testes Python, 63 Node e demais resultados citados no plano v0.2 vêm da avaliação em `5411f62`. O aceite usa apenas os resultados do SHA candidato.
4. **Qualquer mudança após a verificação invalida o que ela afeta.** Corrigir um arquivo exige reconstruir o pacote e repetir os critérios dependentes (seção 5, passo 7).
5. **Comandos neste workspace.** As linhas de comando abaixo seguem o CI. Ao executá-las localmente neste repositório, prefixe cada segmento com `rtk`, conforme `AGENTS.md`.

### Estados de um critério

| Estado | Significado |
|---|---|
| `Verde` | Executado no SHA candidato, resultado esperado, evidência registrada. |
| `Vermelho` | Executado e falhou, ou mutante/caso negativo sobreviveu. Bloqueia. |
| `Pendente` | Artefato ou comando existe, mas não foi executado no SHA candidato. |
| `Ausente` | O artefato ou comando necessário não foi encontrado no repositório. Precisa ser criado antes de verificar. |
| `Registrado` | Existe registro versionado (por exemplo aprovação em `release-policy.yaml`). Foi lido, não reexecutado. Não equivale a `Verde`. |
| `Decisão` | Depende de escolha de mantenedor, não de teste. |

## 2. Estado de partida (instantâneo, não decisão)

Instantâneo do worktree em `8ad5a6d`, 2026-11-25. Origem: leitura dos arquivos citados.

| Item | Valor observado |
|---|---|
| `phase` em `governance/release-policy.yaml` | `legal_approved` |
| Aprovações registradas | `identity` (2026-07-10), `rfc` (2026-08-21, com `review_reference`), `legal` (2026-08-23, com hashes das licenças) |
| Aprovações **não** registradas | `rc`, `final` |
| Material de assinatura registrado | Nenhum campo de fingerprint ou signatário no arquivo de política |
| Versão em `package.json` | `0.1.0` (o padrão vigente é v0.2; ver D-01 na seção 4) |
| Candidato integrado (SHA, digest do pacote) | **Não existe ainda** |

## 3. Matriz de critérios

Coluna **B** indica se o critério é bloqueante para a decisão. Todos os critérios abaixo são bloqueantes, salvo os marcados `não`. Estado inicial usa apenas os estados da seção 1.

### 3.1 Governança e aprovações externas

| ID | Critério verificável | Como verificar | Dono | B | Estado inicial |
|---|---|---|---|---|---|
| G-01 | Aprovação `identity` registrada e política válida contra o schema | `uv run scripts/validate_release_policy.py governance/release-policy.yaml` e `uv run scripts/check_identity.py` | A12 | sim | Registrado (aprovação); execução Pendente |
| G-02 | Aprovação `rfc` com `review_reference` imutável, RFC-001 em `Accepted` | Política válida (G-01); status em `docs/rfcs/accepted-001-v0.2-reconciliation.md` e `RFC_PROCESS.md` | A12 | sim | Registrado |
| G-03 | Aprovação `legal` e licenças íntegras: hashes de `licenses/Apache-2.0.txt` e `licenses/CC-BY-4.0.txt` iguais aos de `licenses/PROVENANCE.json`; `LICENSE-CODE` e `LICENSE-DOCS` presentes; mapa em `licenses/APPLICABILITY.md` cobre os caminhos publicados | Comparar `sha256` dos arquivos com `PROVENANCE.json`. Nenhum script dedicado foi identificado | A11, A12 | sim | Registrado (aprovação); verificação Ausente |
| G-04 | Aprovação `rc` registrada e `phase: rc` válida | Política validada pelo schema (a fase `rc` exige gate `rc`) | Mantenedor | sim | Ausente |
| G-05 | Aprovação `final` registrada e `phase: final` válida | Idem, gate `final`. O plano de 10/10 prevê ainda `governance/final-promotion-approval.yaml`; não existe no repositório | Mantenedor | sim, se a promoção for final (ver D-01) | Ausente |
| G-06 | Assinatura da tag e do pacote por signatário autorizado e fingerprint registrado | Verificação de tag/assinatura com chave pública rastreada. Nenhum fingerprint está registrado | Mantenedor | sim para tag pública | Ausente |
| G-07 | Consistência entre RFC, política, `docs/VERSIONING.md`, changelog e artefatos publicados (versão, fase, aliases, janelas de compatibilidade) | Revisão cruzada com lista de divergências, cada uma resolvida ou aceita por mantenedor | A12 | sim | Pendente |

### 3.2 Segurança de dependências e segredos

| ID | Critério verificável | Como verificar | Dono | B | Estado inicial |
|---|---|---|---|---|---|
| S-01 | Sem vulnerabilidade `moderate` ou acima em dependências Node. Alerta GHSA-mrhx-c7xc-m3w5 (Zod) resolvido, com versões antes/depois e diff do lockfile revisado | `npm ci && npm audit --audit-level=moderate`; `npm run typecheck`; `npm run test:types` | A01 | sim | Pendente |
| S-02 | Sem vulnerabilidade conhecida nas dependências Python | `uv sync --frozen && uv run pip-audit` | A01, A09 | sim | Pendente |
| S-03 | Sem segredo novo nos arquivos rastreados, contra `.secrets.baseline` | `git ls-files -z \| xargs -0 uv run detect-secrets-hook --baseline .secrets.baseline` | A09 | sim | Pendente |
| S-04 | Instalação congelada: lockfiles consistentes com os manifestos | `uv sync --frozen`, `npm ci` sem alterar `uv.lock` nem `package-lock.json` | A09 | sim | Pendente |

### 3.3 Contratos e conformidade

| ID | Critério verificável | Como verificar | Dono | B | Estado inicial |
|---|---|---|---|---|---|
| C-01 | Fixtures golden positivas e negativas conforme | `uv run scripts/validate_conformance.py` | A09 | sim | Pendente |
| C-02 | OpenAPI válido e superfície de referência/segurança conforme | `uv run scripts/validate_openapi.py`; `uv run openapi-spec-validator openapi.yaml` | A06 | sim | Pendente |
| C-03 | Paridade JSON Schema ↔ Zod ↔ DDL, incluindo presença, `null`, defaults, enums, dinheiro e IDs. Uma alteração controlada em só uma representação faz o gate falhar pelo motivo esperado | `uv run scripts/check_contract_parity.py` mais o corpus de A04 | A04 | sim | Pendente (corpus de A04 Ausente) |
| C-04 | Invariantes de domínio Building/Unit/Property | `uv run scripts/check_domain_invariants.py --entities tests/contracts/aligned/entities` | A04 | sim | Pendente |
| C-05 | Testes Python e Node passam | `uv run pytest`; `npm run typecheck`; `npm run test:types` | A09 | sim | Pendente |
| C-06 | Servidor HTTP cumpre o contrato nas operações que declara implementar (payload, referência de schema, autenticação, negação de acesso). Operações apenas especificadas ficam listadas à parte | Testes HTTP de A06 contra `openapi.yaml` e `src/api/server.ts` | A06 | sim | Ausente (testes) |
| C-07 | Compatibilidade de titulares: registros antigos, novos, mistos, copropriedade e conflitos. Migração preserva vínculos e proveniência no round-trip | Matriz e fixtures de A03; verificação em A04 e A05 | A03 | sim | Ausente |
| C-08 | Lacunas de titularidade que exigem decisão normativa estão registradas e tratadas por RFC antes de entrar no contrato | Lista de A03 com decisão de mantenedor para cada item | A03, Mantenedor | sim | Decisão |

### 3.4 Banco de dados (PostgreSQL 16)

| ID | Critério verificável | Como verificar | Dono | B | Estado inicial |
|---|---|---|---|---|---|
| DB-1 | DDL aplica em PostgreSQL 16 limpo | `psql -v ON_ERROR_STOP=1 -f db/schema.sql` (o CI já faz isso) | A05 | sim | Pendente |
| DB-2 | Comportamento da projeção pública: fail-closed, coordenadas ≤ 2 casas, `address_display='hidden'`, imóvel sem listing qualificado ausente | `psql -v ON_ERROR_STOP=1 -f tests/postgres/property_public.sql` | A05 | sim | Pendente. **O `ci.yml` atual não executa este arquivo** |
| DB-3 | Para cada restrição selecionada (FK, coerência Unit/Property, `num_nonnulls`, limite de 100% de participação, `scope='listing'` exige `listing_id`, `trust_tier` 1–6, enum `audit_change_type`), um caso inválido é rejeitado | Testes SQL de A05 | A05 | sim | Ausente (testes além de `property_public.sql`) |
| DB-4 | Migração de dados legados: auditorias da RFC-001 (§Plano de migração) retornam zero linhas após correção; DDL aplicado com registros legados | Consultas da RFC mais fixtures legadas de A03 | A05 | sim | Ausente |

### 3.5 Privacidade operacional

| ID | Critério verificável | Como verificar | Dono | B | Estado inicial |
|---|---|---|---|---|---|
| P-01 | Decisão rastreável da finalidade até a saída por canal; campo restrito ausente na exportação; negação por padrão | Casos sintéticos de A07, sem dados reais | A07 | sim | Ausente |
| P-02 | DSAR com evidência de propagação aos destinos | Caso sintético de A07 | A07 | sim | Ausente |
| P-03 | `docs/privacy-operations.md` separa o que é controle testado do que é obrigação do operador | Revisão: cada controle aponta um teste, ou está marcado como obrigação do operador | A07 | sim | Pendente |

### 3.6 Força dos testes

| ID | Critério verificável | Como verificar | Dono | B | Estado inicial |
|---|---|---|---|---|---|
| T-01 | Cada regra crítica (dinheiro, identidade, titularidade, política, projeção) tem cobertura catalogada e ao menos uma mutação isolada, em cópia temporária | Catálogo e harness de A08 | A08 | sim | Ausente |
| T-02 | Cada mutação obrigatória faz o gate específico falhar. Mutante sobrevivente aparece no relatório e impede o aceite daquela regra | Relatório do harness | A08 | sim | Ausente |

### 3.7 Reprodução e CI

| ID | Critério verificável | Como verificar | Dono | B | Estado inicial |
|---|---|---|---|---|---|
| R-01 | CI verde no SHA candidato, com link de execução guardado. Jobs atuais: `conformance` e `contracts` | Execução de `.github/workflows/ci.yml` no SHA | A09 | sim | Pendente |
| R-02 | Clone limpo local no mesmo SHA produz os mesmos resultados que o CI (instalação congelada, auditoria, testes, conformidade, governança, SQL) | Roteiro executável único de verificação. Não existe agregador no repositório | A09 | sim | Ausente (roteiro) |
| R-03 | Todo check novo entregue por A04–A08 está integrado ao workflow | Diff do workflow versus lista de comandos desta matriz | A09 | sim | Pendente |

### 3.8 Documentação e autoridade

| ID | Critério verificável | Como verificar | Dono | B | Estado inicial |
|---|---|---|---|---|---|
| DOC-01 | Em um único percurso o leitor encontra a norma vigente (v0.2), os aliases históricos, a regra de resolução de divergências e o comando de validação | Leitura do `README.md` em clone limpo; links, nomes de jobs e comandos conferidos | A02 | sim | Pendente |
| DOC-02 | Migração v0.1.0 → v0.2 documentada para cada mudança breaking da RFC-001 | `docs/migrations/v0.1.0-to-v0.2.md` confrontado com a RFC | A02, A12 | sim | Pendente |
| DOC-03 | Changelog ou release notes da versão candidata existe e cobre cada mudança com impacto de compatibilidade | `CHANGELOG*` não foi encontrado no repositório | A12 | sim | Ausente |
| DOC-04 | Artefatos de comunidade exigidos para publicação pública (segurança, contribuição) existem, se o mantenedor os mantiver como exigência | `SECURITY*` e `CONTRIBUTING*` não foram encontrados. O plano de 10/10 os menciona como parte do escopo | Mantenedor | não, até decisão | Decisão |

### 3.9 Consumidor independente

| ID | Critério verificável | Como verificar | Dono | B | Estado inicial |
|---|---|---|---|---|---|
| I-01 | Consumidor em diretório separado, implementado a partir da norma e dos exemplos, sem importar validadores, mapeadores ou resultados internos | Inspeção de imports e árvore do consumidor | A10 | sim | Ausente |
| I-02 | Processa imóvel, anúncio e exposição; aceita o exemplo válido e rejeita o inválido; resultados coincidem com os do candidato | Execução do consumidor sobre `examples/` e `tests/golden/` | A10 | sim | Ausente |
| I-03 | Toda interpretação ambígua da norma está registrada, cada uma com encaminhamento | Relatório de A10 | A10 | sim | Ausente |
| I-04 | I-02 repetido contra os **bytes do pacote** final, não contra o checkout | Execução sobre o pacote extraído | A10 | sim | Ausente |

### 3.10 Pacote

| ID | Critério verificável | Como verificar | Dono | B | Estado inicial |
|---|---|---|---|---|---|
| K-01 | Inventário do conteúdo público, com versão, licença e proveniência por componente | Manifesto do pacote | A11 | sim | Ausente (não há construtor de pacote no repositório) |
| K-02 | Pacote extraído funciona fora do checkout e informa versão e licença dos componentes | Extração em diretório limpo e execução da verificação | A11 | sim | Ausente |
| K-03 | Verificação de hashes passa; alterar um byte faz falhar | Verificador de integridade e teste de adulteração | A11 | sim | Ausente |
| K-04 | O pacote foi gerado do mesmo SHA que o CI validou, e o digest está registrado | Comparar SHA do pacote com o SHA do R-01 | A11, A12 | sim | Ausente |

## 4. Decisões abertas para o mantenedor

Estas decisões não podem ser tomadas por automação nem inferidas dos arquivos. Cada uma precisa de resposta registrada antes da decisão de release.

| ID | Questão | Por que está aberta |
|---|---|---|
| D-01 | **Qual versão e qual fase serão publicadas?** | O plano v0.2 trata de "candidato público" do padrão v0.2. `package.json` está em `0.1.0`. O plano de 10/10 descreve o caminho `rc` → `final` com tag `v1.0.0`, e a RFC-001 rejeita publicar v1.0.0 diretamente. A política tem as fases `rc` e `final`, mas nada diz qual delas esta entrega alvo. |
| D-02 | O plano v0.2 passa a ter trava de imutabilidade? | `governance/plan-lock.json` fixa apenas `docs/plans/pibras-10-of-10-public-standard.md`. Este plano não está travado. |
| D-03 | Quais obrigações de comunidade (segurança, contribuição) são exigidas para a primeira publicação? | Ver DOC-04 na seção 3.8. |
| D-04 | Que sinal de interoperabilidade externa basta? | A RFC-001 cita "evidência de interoperabilidade externa" como requisito de v1.0.0. O plano v0.2 define um consumidor de teste (A10), que é interno ao projeto. Se isso satisfaz ou não a exigência é decisão de mantenedor. |
| D-05 | Material de assinatura: quem assina e com qual chave? | Nenhum fingerprint ou signatário consta na política. |

### Inconsistências documentais a resolver (A02/A12)

Observadas na leitura. Nenhuma foi corrigida aqui, pois este documento não altera artefatos de outros donos.

1. A RFC-001 afirma que todos os gates "rodam em CI a cada PR", inclusive `tests/postgres/property_public.sql`. O `ci.yml` atual aplica `db/schema.sql`, mas não executa esse arquivo.
2. A RFC-001, em "Questões abertas" item 3, diz que o licenciamento permanece bloqueante e que `LICENSE` está em "License decision pending". A política registra a aprovação legal de 2026-08-23. O texto da RFC está desatualizado em relação à política.
3. A tabela de `docs/VERSIONING.md` lista os arquivos da v0.2 e não menciona `licenses/` nem a política de release. Confirmar se isso é intencional.

## 5. Processo de decisão

```txt
1. Congelar o candidato
2. Verificar no SHA integrado
3. Construir o pacote a partir do SHA verde
4. Repetir o exercício independente contra o pacote
5. Consolidar o relatório de decisão
6. Decidir
7. Tratar mudanças posteriores
```

### Papéis

| Papel | Faz | Não faz |
|---|---|---|
| Integrador | Registra o SHA inicial, integra entregas, encaminha cada falha ao dono do arquivo, registra à parte as decisões que dependem de mantenedor ou de evidência operacional externa | Aprovar release |
| Dono do critério (A01–A11) | Entrega diff ou relatório, comando reproduzível, resultado e pendências | Marcar o próprio critério como aceito sem evidência |
| A12 (revisão de lançamento) | Repete as verificações críticas no SHA integrado, confere teste independente, integridade do pacote e aprovações exigidas, e emite o relatório de decisão com bloqueios, responsáveis e reprodução | Decidir a promoção |
| Mantenedor | Decide a promoção conforme `docs/VERSIONING.md` e `governance/release-policy.yaml`; responde as decisões da seção 4; registra aprovações com `review_reference` | Delegar a aprovação a automação |

### Passos

1. **Congelar o candidato.** O integrador anota o SHA. A partir daqui, qualquer commit novo reabre o passo 2 para os critérios afetados.
2. **Verificar no SHA integrado.** Cada dono executa seus critérios (seção 3) e registra evidência (seção 6). A12 repete por conta própria os critérios críticos: S-01, C-01 a C-05, DB-1, DB-2, R-01 e R-02. Resultado de dono e resultado de A12 precisam coincidir.
3. **Construir o pacote.** A11 gera o pacote a partir do SHA que ficou verde. O pacote de ensaio pode ser descartado e reconstruído até a decisão.
4. **Repetir o exercício independente.** A10 roda I-02 contra os bytes do pacote (I-04). K-03 e K-04 são conferidos.
5. **Consolidar.** A12 produz o relatório com uma linha por critério da matriz, o estado final, o link da evidência, os bloqueios com responsável e as decisões abertas da seção 4.
6. **Decidir.** O mantenedor aplica as regras abaixo e registra a decisão (seção 7).
7. **Tratar mudanças posteriores.** Qualquer correção após o passo 2 exige novo SHA, reconstrução do pacote e repetição dos critérios afetados. Uma aprovação registrada para um SHA não vale para outro.

### Regras de decisão

| Resultado | Condição |
|---|---|
| **Bloqueado** | Qualquer critério bloqueante em `Vermelho`, `Pendente` ou `Ausente`; qualquer decisão da seção 4 sem resposta que afete a fase alvo; SHA do pacote diferente do SHA validado no CI; divergência entre o resultado do dono e o de A12. |
| **Pronto para decisão** | Todos os critérios bloqueantes `Verde` no mesmo SHA, e as decisões da seção 4 respondidas. Isto **não** é aprovação: apenas autoriza o mantenedor a decidir. |
| **Promovido** | Mantenedor registra a aprovação do gate da fase alvo (`rc` ou `final`) em `governance/release-policy.yaml`, com `approver`, `date` e `review_reference`, e a política continua válida contra o schema. Tag pública e assinatura só depois, usando versão e autorização dessa etapa. |
| **Adiado** | Mantenedor decide não promover apesar de estar pronto. Registrar o motivo. |

### Dispensas

Um critério bloqueante só pode ser dispensado pelo mantenedor, por escrito, com: ID do critério, motivo, risco aceito, escopo (SHA e versão) e referência imutável (PR, commit ou ata). A dispensa vale apenas para aquele SHA. Critérios de G-01 a G-06 e S-01 não admitem dispensa por este processo.

## 6. Registro de evidência

Uma linha por execução. Nenhuma linha foi preenchida: não há candidato integrado.

| Critério | SHA | Comando | Saída (código) | Data | Executor | Local da saída/link |
|---|---|---|---|---|---|---|
| | | | | | | |

## 7. Registro de decisão

### Modelo

```md
## Decisão de release <versão> | <data>

- SHA candidato:
- Digest do pacote:
- Fase alvo (rc | final):
- Relatório de A12 (referência):
- Critérios bloqueantes não verdes (ID, responsável):
- Dispensas (ID, motivo, risco aceito, referência):
- Decisões da seção 4 respondidas (ID, resposta, referência):
- Resultado: Bloqueado | Pronto para decisão | Promovido | Adiado
- Mantenedor:
- Referência imutável da aprovação:
```

### Decisões registradas

Nenhuma. Estado atual: **não decidido**. Não existe candidato integrado, e vários critérios bloqueantes estão `Ausente` ou `Pendente` (seção 3).

## 8. Manutenção deste documento

- Mudar a matriz, as regras de decisão ou os critérios de dispensa é mudança de governança: registrar por RFC ou PR de mantenedor.
- Quando A09 entregar um roteiro agregado, substituir os comandos individuais da seção 3 por ele e manter a lista aqui como referência de cobertura.
- Ao criar `CHANGELOG`, construtor de pacote, harness de mutação ou consumidor independente, atualizar o estado inicial dos critérios correspondentes. Estado inicial só muda para `Verde` por meio de evidência na seção 6.
