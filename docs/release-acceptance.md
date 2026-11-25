# Aceite da distribuição PIBRAS v0.2

O candidato é identificado por um commit Git e pelo SHA-256 do ZIP construído daquele commit. O mantenedor usa os dois identificadores para decidir a promoção conforme a [política](../governance/release-policy.yaml), o [versionamento](VERSIONING.md) e a [RFC aceita](rfcs/accepted-001-v0.2-reconciliation.md).

| Critério | Evidência exigida | Decisão se falhar |
|---|---|---|
| Dependências e contratos | Os dois jobs de CI e os modos locais `conformance` e `contracts` de `scripts/qa/verify.sh` concluem no mesmo SHA. Auditorias npm e Python, testes HTTP e validações de identidade e governança passam. | Corrigir a dependência ou o contrato e revalidar. |
| Migração | A matriz de titulares cobre legado, canônico, misto, copropriedade e conflito. Round-trip preserva campos de origem e vínculos. | Manter a compatibilidade vigente e corrigir o mapeamento. |
| Implementações | Registrar linhas de paridade, observações conhecidas, cinco mutações detectadas e resultados SQL em PostgreSQL 16 descartável. | Encaminhar divergência semântica à RFC aplicável. Aplicar a decisão de escopo monetário registrada abaixo. |
| Privacidade | Relacionar a decisão de exposição ao resultado em cada canal e a evidência de DSAR à operação. O operador guarda as evidências próprias de processo. | Registrar o controle afetado e corrigir a exposição ou a falta de evidência. |
| Pacote e consumidor | Duas construções do mesmo commit têm bytes idênticos. Verificação e consumidor independente passam fora do checkout. A alteração de um byte é rejeitada. Ver [procedimento](PACKAGE.md). | Reconstruir o pacote a partir do commit corrigido e repetir o ensaio. |
| Publicação | Registrar aprovação de promoção e assinatura pelo mantenedor para a versão escolhida. Verificar licenças, proveniência e impacto listado no changelog. | Manter o pacote como ensaio local até a decisão. |

O registro de execução contém commit, digest, URL da CI, comandos, códigos de saída, pendências e signatário quando aplicável. Guardá-lo fora do conteúdo usado para calcular o próprio digest. Atualizar o registro quando o candidato mudar.

## Registro da candidata v0.2.0 — publicação pendente

**Decisão de escopo.** Preservar o contrato base e suas observações de compatibilidade: fora da faixa segura do JavaScript, não declarar paridade entre JSON Schema e Zod. A garantia de paridade monetária vale para o perfil de intercâmbio optativo `money-safe-v1`; em JavaScript, validar o texto original com `parseSafeMoneyJson(raw)`. A [RFC de Money/Settlement](rfcs/draft-money-settlement.md) permanece draft e seu algoritmo de rateio não é requisito da norma.

**Evidência da candidata.** O recibo externo no PR de promoção deve vincular o SHA completo à execução de CI e ao SHA-256 integral do ZIP, conferido por construção independente. Esse recibo fica fora do pacote para não criar uma referência circular. Se o commit mudar, inclusive por merge, repetir a CI e a conferência do digest antes da assinatura.

**Estado.** Candidata preparada para revisão; assinatura, tag estável e publicação pendentes. O aceite desta decisão de escopo não equivale a autorização de publicação.
