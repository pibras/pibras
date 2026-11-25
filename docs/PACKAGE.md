# Ensaio local de distribuição

O kit distribui a norma e o corpus de interoperabilidade. Não é um checkout de desenvolvimento, pacote npm/PyPI, implantação de servidor ou release assinada. Não incorpora dependências de terceiros. Manifests de projeto identificam componentes, não instruem a instalar o kit. O exercício do consumidor e a verificação de bytes exigem apenas Python ≥ 3.11.

Com Git e Python, na raiz do repositório, registre o SHA exato aprovado nos testes. Use arquivos novos e o construtor desse mesmo SHA. O construtor lê blobs Git; arquivos modificados ou não rastreados não entram. Exemplo:

```sh
SHA=$(git rev-parse HEAD)
D=$(mktemp -d)
python3 scripts/public_package.py build "$SHA" "$D/ensaio.zip"
python3 scripts/public_package.py build "$SHA" "$D/repeticao.zip"
cmp "$D/ensaio.zip" "$D/repeticao.zip"
python3 -m zipfile -e "$D/ensaio.zip" "$D/extraido"
(cd "$D/extraido" && python3 scripts/public_package.py verify .)
```

O comando de construção imprime o SHA-256 do ZIP integral e o commit de origem. Antes de executar qualquer código de uma cópia recebida, compare o digest do ZIP com o digest obtido por um canal confiável. O manifesto interno detecta corrupção, não autentica o remetente nem substitui assinatura.

**Inventário:** norma, RFCs e documentação (exceto planos internos), OpenAPI, schemas, tipos, DDL, mapeamentos, exemplos, casos golden, metadados de versão/política/licenças e ferramentas isoladas de consumo e verificação. O inventário efetivo por caminho e a versão declarada de cada contrato/projeto estão em `PACKAGE-MANIFEST.json`; o SHA Git identifica de forma inequívoca as revisões dos componentes sem versão própria. Registros de licença seguem `licenses/APPLICABILITY.md`; as cópias dos textos são conferidas contra `licenses/PROVENANCE.json`. A inclusão de um draft não o promove à norma.

**Teste negativo:** em uma segunda extração, altere um byte de um exemplo. O comando `verify` deve terminar com status diferente de zero. A verificação também rejeita omissões, arquivos adicionais e links simbólicos. Não execute os testes adicionando caches ou relatórios ao diretório que deseja verificar.
