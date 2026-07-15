# Operações de privacidade: fluxo controlado

## 1. Escopo e força normativa

Este documento traduz requisitos de proteção de dados em controles operacionais para
implementações PIBRAS, inclusive integrações hub-and-spoke, enriquecimento, importação de
legado e atendimento a titulares. Ele não substitui análise jurídica do caso concreto.

Os termos normativos têm o seguinte significado:

- **MUST**: requisito da LGPD ou condição indispensável para alegar conformidade legal;
- **POLICY-SHALL**: controle mínimo adotado pelo PIBRAS, ainda que a LGPD não prescreva
  literalmente aquele mecanismo técnico ou contratual;
- **SHOULD**: prática recomendada, cujo afastamento precisa ser justificado e registrado;
- **MAY**: opção permitida, sujeita aos demais requisitos deste documento.

O objetivo não é liberar todo fluxo nem bloquear todo dado pessoal. Cada operação **MUST**
ter finalidade legítima, específica e informada, hipótese legal aplicável, necessidade,
segurança, transparência e prestação de contas. A implementação **POLICY-SHALL** bloquear a
operação quando não conseguir demonstrar esses elementos.

## 2. Regra de decisão

Antes de coletar, enriquecer, consultar, transferir ou eliminar dados pessoais, o controlador:

1. **MUST** identificar a finalidade e a hipótese legal aplicável;
2. **MUST** limitar o tratamento ao necessário para a finalidade;
3. **MUST** identificar os agentes e suas responsabilidades reais no caso concreto;
4. **MUST** informar o titular conforme a LGPD e viabilizar seus direitos;
5. **MUST** adotar medidas técnicas e administrativas proporcionais ao risco;
6. **POLICY-SHALL** registrar a decisão, a versão da política e evidências da execução;
7. **POLICY-SHALL** negar o fluxo quando finalidade, hipótese legal, destinatário ou
   conjunto mínimo de campos não estiverem definidos.

Consentimento é uma entre as hipóteses legais do art. 7º. A implementação **MUST NOT**
usar consentimento como rótulo genérico nem presumir que outra hipótese legal dispensa os
princípios do art. 6º.

## 3. Classificação por risco

CPF é dado pessoal, mas não é, por si só, dado pessoal sensível na lista taxativa do art. 5º,
II. O PIBRAS o classifica como **dado pessoal comum restrito**, por risco de fraude e dano.
Scores financeiros vinculados a pessoa identificada ou identificável também são dados
pessoais e **MUST** ser classificados conforme finalidade, origem, impacto e contexto.

Para CPF e outros identificadores de alto impacto:

- o uso **MUST** ser necessário e compatível com a finalidade registrada;
- logs, telemetria, mensagens de erro e evidências de suporte **POLICY-SHALL NOT** conter o
  valor em claro;
- exportações genéricas e ambientes não produtivos **POLICY-SHALL** usar dados sintéticos,
  supressão ou mascaramento adequado;
- screenshots e material de treinamento **POLICY-SHALL NOT** expor o valor;
- hashing **MUST NOT** ser apresentado como anonimização quando ainda for razoavelmente
  possível associar o resultado a uma pessoa; nesse cenário, trata-se de pseudonimização e a
  LGPD continua aplicável.

## 4. Enriquecimento, scoring e decisões automatizadas

Enriquecimento **MAY** ocorrer quando houver hipótese legal e compatibilidade com a
finalidade informada. Legítimo interesse só se aplica a dados pessoais não sensíveis e
**MUST** observar finalidade, necessidade, legítimas expectativas, direitos e liberdades do
titular, transparência e salvaguardas.

Quando o controlador escolher legítimo interesse:

- **POLICY-SHALL** manter avaliação documentada de legítimo interesse, incluindo teste de
  finalidade, necessidade e balanceamento/salvaguardas, conforme o guia da ANPD;
- **MUST** tratar somente os dados estritamente necessários e garantir transparência;
- **MUST** manter registro da operação, especialmente por essa hipótese legal;
- **SHOULD** elaborar ou atualizar RIPD quando o risco elevado justificar, sem prejuízo das
  hipóteses em que a ANPD o exigir.

Proteção do crédito **MUST NOT** ser usada como fundamento genérico para priorização
comercial. Ela **MAY** fundamentar operação efetivamente vinculada a proteção do crédito,
após análise do caso concreto.

Decisão tomada unicamente com base em tratamento automatizado que afete interesses do
titular **MUST** oferecer canal para o exercício do direito de solicitar revisão e **MUST**
fornecer, quando solicitado, informações claras e adequadas sobre critérios e procedimentos,
resguardados os segredos comercial e industrial. Intervenção humana **SHOULD** ser oferecida
como salvaguarda quando proporcional ao risco, mas este documento não a declara requisito
textual universal do art. 20.

## 5. Compartilhamento hub-and-spoke

Compartilhar é operação de tratamento e não é automaticamente incidente de segurança. O
controlador **MUST** demonstrar a licitude do compartilhamento e aplicar finalidade,
adequação, necessidade, transparência, segurança e responsabilização.

Papéis de controlador, controlador conjunto, operador e suboperador **MUST** refletir quem
efetivamente toma decisões e executa o tratamento; nomenclatura contratual isolada não altera
a realidade. Antes de habilitar um spoke:

- a função de cada agente **POLICY-SHALL** estar registrada;
- instrumento contratual com obrigações de privacidade e segurança **POLICY-SHALL** estar
  vigente e compatível com os papéis reais;
- finalidade, hipótese legal, retenção, descarte e eventual transferência internacional
  **MUST** estar avaliados;
- mecanismo de propagação de solicitações de titulares **POLICY-SHALL** estar testado;
- o destinatário e cada evento de compartilhamento **POLICY-SHALL** ser auditáveis.

Um contrato de processamento ou cláusula de proteção de dados não torna, sozinho, o fluxo
lícito. Da mesma forma, este documento não afirma que a LGPD nomeia um "DPA" como requisito
formal universal para todo compartilhamento; o instrumento é um controle obrigatório da
política PIBRAS.

### 5.1 Sync Service

O Sync Service é o ponto de enforcement de referência. Autorizações internas do CRM não são
suficientes para controlar dados após a saída do hub.

Para cada transferência, o Sync Service **POLICY-SHALL**:

1. validar finalidade, hipótese legal, parceiro, papel e status contratual;
2. aplicar allowlist versionada de campos, ação e canal, com default-deny;
3. registrar origem, destino, finalidade, base, política, campos ou classificação do payload,
   horário, resultado e identificador de correlação, sem duplicar PII no log;
4. impedir campos não autorizados, ainda que o usuário possua acesso interno;
5. suportar revogação, retenção, purge e propagação de DSAR;
6. produzir `reason_code` auditável para allow, deny, mask ou needs_approval.

O ledger **SHOULD** registrar referências aos registros compartilhados em vez de copiar seus
valores pessoais. A allowlist **MUST NOT** substituir a avaliação legal; ela prova e executa a
decisão previamente governada.

## 6. Legado e higiene de superfícies

Idade do dado, isoladamente, não define licitude. Antes da importação de legado, o
controlador **MUST** verificar origem, hipótese legal, finalidade original, compatibilidade da
finalidade atual, qualidade, retenção e informação ao titular. Dados sem origem ou fundamento
demonstrável **POLICY-SHALL NOT** entrar no acervo operacional.

Importações **SHOULD** ocorrer em ondas com métricas de rejeição, duplicidade, oposição,
qualidade e purge. Uma importação em massa **MAY** ser adotada somente quando sua avaliação
de risco e controles equivalentes estiverem documentados.

PII **POLICY-SHALL NOT** aparecer em logs genéricos, traces, dumps, analytics, tickets,
screenshots ou datasets de desenvolvimento. Exceções operacionais indispensáveis **MUST**
ter escopo, acesso, retenção e auditoria específicos.

## 7. Direitos, retenção e incidentes

Solicitações do titular **MUST** ser autenticadas de forma proporcional, registradas,
respondidas nos termos e prazos aplicáveis e propagadas aos operadores ou destinatários
relevantes quando necessário. A implementação **POLICY-SHALL** preservar evidência de
recebimento, decisão, execução e registros afetados sem reter desnecessariamente o próprio
dado objeto da solicitação.

Retenção **MUST** estar ligada a finalidade e fundamento válidos. Ao término, o sistema
**POLICY-SHALL** executar a ação definida (`delete`, anonimização efetiva, revisão ou arquivo
legalmente justificado) e registrar o resultado.

Incidente de segurança **MUST** ser avaliado segundo risco ou dano relevante. Quando
configurados os requisitos legais e regulatórios, o controlador **MUST** comunicar a ANPD e
os titulares nos termos aplicáveis; o ledger e os logs **SHOULD** permitir reconstrução sem
ampliar o vazamento.

## 8. Gate mínimo de produção

Um piloto **POLICY-SHALL NOT** escalar para produção até existir evidência de:

- inventário de finalidade, hipótese legal, campos e destinatários;
- papéis dos agentes e instrumento contratual vigente;
- aviso de privacidade coerente com enriquecimento e compartilhamento;
- avaliação documentada quando usado legítimo interesse;
- allowlists e default-deny testados;
- sharing ledger sem PII desnecessária;
- DSAR, retenção, purge e resposta a incidente testados;
- proprietário do controle, revisão periódica e procedimento de revogação.

## 9. Fontes oficiais

- [Lei nº 13.709/2018 — LGPD, texto oficial](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm), especialmente arts. 5º, 6º, 7º, 10, 18, 20, 37, 38, 46 e 48.
- [ANPD — Guia Orientativo das Hipóteses Legais de Tratamento de Dados Pessoais: Legítimo Interesse](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes/guia_orientativo_hipoteses_legais_tratamento_de_dados_pessoais_legitimo_interesse).
- [ANPD — Guia para Definições dos Agentes de Tratamento e do Encarregado, versão 2.0](https://www.gov.br/anpd/pt-br/assuntos/noticias/nova-versao-do-guia-dos-agentes-de-tratamento).
- [ANPD — Relatório de Impacto à Proteção de Dados Pessoais](https://www.gov.br/anpd/pt-br/canais_atendimento/agente-de-tratamento/relatorio-de-impacto-a-protecao-de-dados-pessoais-ripd).
- [ANPD — Materiais educativos e publicações](https://www.gov.br/anpd/pt-br/centrais-de-conteudo/materiais-educativos-e-publicacoes).

