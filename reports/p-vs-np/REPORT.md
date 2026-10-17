# Validação do exemplo do Clay e do ambiente AXIOM

Consulta às fontes: 17 de outubro de 2026. Escopo confirmado pelo usuário:
validar o exemplo e o ambiente. **Nenhuma demonstração de P = NP ou P ≠ NP foi
fornecida ou produzida.** O Clay continua classificando o problema como aberto.
[Fonte oficial](https://www.claymath.org/millennium/p-vs-np/).

## Exemplo combinatório

O exemplo do Clay considera escolher 100 alunos entre 400, respeitando uma lista
de incompatibilidades. A quantidade de grupos candidatos, antes de aplicar essas
restrições, é:

```text
C(400, 100) =
2241854791554337561923210387201698554845411177476295990399942258896013007429693894018935107174320
```

Isso corresponde a aproximadamente **2,24 × 10^96 grupos candidatos**.
Dentro de um grupo de 100 alunos há **C(100, 2) = 4.950 pares distintos** cuja
compatibilidade pode ser consultada. As duas chamadas retornaram
`guarantee = exact-symbolic`, `verification.passed = true` e `max_error = 0`.
Ambos os valores também coincidiram exatamente com `math.comb` da biblioteca
padrão do Python, uma implementação distinta da `sympy.binomial` usada pelo AXIOM.

A revisão do código na versão preliminar avaliada mostrou que o verificador interno de teoria dos números
terminava em uma aprovação genérica para operações como `binomial`, sem recalcular
o coeficiente. Portanto, o rótulo do AXIOM isoladamente não constituía essa segunda
conferência; ela foi executada explicitamente neste trabalho.

> **Nota de Versão (v0.2.1 / v0.2.2)**: Esta limitação histórica foi superada a partir da v0.2.1. O verificador interno `verify_number_theory` agora executa recálculo ortogonal mandatório contra `math.comb` da biblioteca padrão e a identidade da recorrência de Pascal (`kind = binomial-comb-and-pascal-check`), conferindo garantia exata e reprodutível diretamente pelo motor.


Não foi fornecida uma lista concreta de incompatibilidades. Não se determinou
quais grupos são válidos nem se existe um grupo válido para uma instância
específica. A contagem também não estabelece um limite inferior para todos os
algoritmos possíveis. P vs NP trata de classes de problemas e limites de tempo
para entradas de tamanho arbitrário.
[Enunciado de Stephen Cook, páginas 1–2](https://www.claymath.org/wp-content/uploads/2022/06/pvsnp.pdf).

## Ambiente e controles executados

| Verificação | Resultado observado |
| --- | --- |
| Código carregado | `src/axiom` deste repositório |
| Python / SymPy / mpmath | 3.14.7 / 1.14.0 / 1.3.0 |
| `doctor` | `ok: true`; 7 de 7 autotestes aprovados |
| MCP por stdio | Inicialização, listagem de 21 ferramentas e chamada de `math_number_theory` funcionaram |
| Resultado combinatório via MCP | `exact-symbolic`; `verification.passed: true`; igual à CLI e a `math.comb` |
| Raiz incorreta `x = 4` em `x^2 - 5*x + 6 = 0` | Refutada; `unverified`; `verification.passed: false`; resíduo 2 |
| Lean / Lake | Não encontrados no PATH nem em `~/.elan/bin` pelo AXIOM |
| Provas de controle em `examples/theorems.lean` | `unverified`; `verification.passed: false`; kernel não executado |
| SDK Python `mcp` | Ausente; o transporte stdio nativo funcionou sem ele |
| Sage / Julia / SciPy / matplotlib | Não detectados; não necessários para este exemplo |

Os 11 critérios do script de validação passaram. Isso inclui confirmar a resposta
correta **de indisponibilidade** do Lean; não significa que a verificação formal
passou. Da mesma forma, `doctor.ok: true` não significa que todos os motores estão
instalados. Os motores listados no registro podem ser adaptadores sem executável.

Uma sondagem adicional, `verify "2 + 2 = 5"`, retornou erro genérico de entrada,
`unverified` e nenhum campo `verification`, em vez de uma refutação estruturada.
Essa limitação está preservada nas evidências. O controle com raiz incorreta
efetivamente percorreu a verificação por substituição e produziu uma refutação.

`ok: true` no resultado Lean e no da raiz incorreta indica que a operação retornou
normalmente; não indica uma afirmação matemática comprovada. É necessário ler
`guarantee` e `verification.passed`.

## Reprodução e evidências

Na raiz do repositório:

```powershell
python reports/p-vs-np/validate.py
```

O script [validate.py](validate.py) grava [validation.json](validation.json) com
os resultados integrais, `evidence`, `reproducible_with`, argumentos completos,
requisições e respostas MCP, conferências independentes e hashes SHA-256 dos
arquivos relevantes. A data/hora de execução vem do relógio do ambiente.

Comandos individuais:

```powershell
python -m axiom.cli doctor --json
python -m axiom.cli number-theory binomial -n 400 -k 100 --json
python -m axiom.cli number-theory binomial -n 100 -k 2 --json
python -m axiom.cli verify "x^2 - 5*x + 6 = 0" --solutions 4 --variable x --json
python -m axiom.cli prove examples/theorems.lean --engine lean --json
```

O comando `axiom` não foi encontrado no PATH; `python -m axiom.cli` funcionou.
`python -m axiom` não funciona nesta versão porque não há módulo `axiom.__main__`.
O comando registrado automaticamente para `number-theory` omite `n` e `k`; os
comandos completos acima e no JSON permitem reproduzir exatamente a execução.

Foram criados apenas os arquivos deste relatório. Não foram instaladas
dependências nem alterados os arquivos de implementação. As alterações
preexistentes em `src/axiom/contract.py` e `src/axiom/parsing.py` foram preservadas.

Para uma futura validação formal de P vs NP seriam necessários uma demonstração
candidata, definições adequadas de classes de complexidade e um ambiente Lean
operacional. Escrever apenas `P = NP` no parser de álgebra não define essas classes.
