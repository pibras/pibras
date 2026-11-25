# PostgreSQL 16 descartável

Na raiz, execute `bash tests/postgres/run.sh` com Docker, ou indique os binários
locais 16: `PG_BINDIR=/opt/homebrew/opt/postgresql@16/bin bash tests/postgres/run.sh`.
O modo local requer um usuário não-root, cria um cluster em diretório privado e
escuta apenas em socket Unix; o contêiner não publica portas. O runner não usa
um banco existente. Em ambos os modos ele imprime a versão, aplica o DDL do zero,
executa cada arquivo SQL com parada no primeiro erro e remove a instância na saída.

- **Unit/Property:** a FK composta aplica PIBRAS-INV-002 inclusive quando apenas
  um edifício é nulo. A validação diferida permite corrigir as duas pontas na
  mesma transação. Dados históricos divergentes precisam de reconciliação antes
  de aplicar restrição equivalente em uma instalação existente; não há migração
  automática de produção.
- **Titularidade:** grava os dois cotitulares legados do corpus A03, conserva a
  tabela antiga, compara vínculos, identificadores e proveniência persistidos e
  aceita vínculo canônico na Unit. Verifica FKs, exclusividade Unit/Property e
  soma ativa em uma transação. O cálculo de UUID e a resolução/quarentena de
  conflitos do importador não são responsabilidade do DDL.
- **Projeção:** testa a view pública, mascaramento de preço/endereço, precisão
  reduzida, alteração das tabelas de origem e revogação, com dados sintéticos.
