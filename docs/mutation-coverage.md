# Força dos testes de execução

Após a instalação congelada das dependências, execute `uv run --frozen python scripts/qa/check_mutations.py`.
Cada regra tem um controle verde e uma única mudança de implementação em uma nova cópia temporária. A suíte roda o mesmo teste antes e depois, usando as dependências Node instaladas. Nada é alterado no checkout. A saída identifica a regra, o resultado e o nome do teste.

| Regra | Alteração exercitada | Observação exigida |
| --- | --- | --- |
| Dinheiro | Remover a exigência de centavos inteiros no Zod | Rejeição de 10,5 centavos |
| Identidade da unidade | Não normalizar a pontuação da matrícula recebida | Correspondência exata, sem depender de endereço ou área |
| Titularidade | Permitir omitir party_id em Ownership | Vínculo válido com a parte, inválido sem ela |
| Política de exposição | Tratar decisão pendente de aprovação como publicável | Nenhuma projeção enquanto aguarda aprovação |
| Projeção por canal | Permitir matrícula fora da lista de campos do portal | Somente headline e id na saída sintética |

Somente falha de asserção no teste nominal conta como `KILLED`. `SURVIVED` (teste ainda verde), erro de ambiente, falha do controle ou ponto de mutação obsoleto impedem o aceite. O resultado mede essas cinco regressões, não uma porcentagem geral de cobertura nem a conformidade do operador. Migração, PostgreSQL e projeção schema.org têm gates próprios.
