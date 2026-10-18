# P vs NP — Investigação e Validação AXIOM

- Registro: 18 de outubro de 2026.
- Situação matemática: **Em aberto**, conforme a [página oficial do Clay](https://www.claymath.org/millennium/p-vs-np/).
- Situação da investigação: Exemplo combinatório, barreiras clássicas da complexidade (Relativização, Provas Naturais, Algebrização), arithmetização de Cook-Levin e espectro de Hao Huang avaliados; nenhuma demonstração de P = NP ou P ≠ NP fornecida ou produzida.
- Referência técnica: [Descrição oficial por Stephen Cook](https://www.claymath.org/wp-content/uploads/2022/06/pvsnp.pdf).

## Descrição do Clay Mathematics Institute

> If it is easy to check that a solution to a problem is correct, is it also easy to solve the problem? This is the essence of the P vs NP question. Typical of the NP problems is that of the Hamiltonian Path Problem: given N cities to visit, how can one do this without visiting a city twice? If you give me a solution, I can easily check that it is correct. But I cannot so easily find a solution.

## Documentos e Artefatos da Pesquisa

- [Monografia Científica Completa](RESEARCH.md): Análise detalhada das três barreiras estruturais (BGS 1975, Razborov-Rudich 1997, Aaronson-Wigderson 2008), experimentos de arithmetização, teorema de sensibilidade de Huang (2019) e avaliação crítica do motor AXIOM.
- [Relatório Consolidado de Validação](REPORT.md): Tabela de 18 critérios executados, métricas dinâmicas (100% fail-closed) e comandos de reprodução.
- [Resultados da Investigação](investigation_results.json): Registro serializado de todas as execuções experimentais.
- [Evidências Canônicas](validation.json): Registro integral gerado por `validate.py` com hashes SHA-256 e saídas das ferramentas.
- [Script de Investigação Experimental](investigation.py): Executa simulação das barreiras, decomposição espectral e benchmarks 3-SAT.
- [Script de Reprodução da Validação](validate.py): Suíte oficial de validação em 18 critérios integrada ao Millennium Bench.

Esses arquivos registram o trabalho analítico, computacional e suas limitações epistemológicas. Não constituem uma solução do problema em aberto do Clay.

## Como Reproduzir

```powershell
# Execução da investigação experimental detalhada:
python reports/p-vs-np/investigation.py

# Validação canônica dos 18 critérios:
python reports/p-vs-np/validate.py

# Benchmark consolidado dos 7 Problemas do Milênio:
python benchmarks/millennium/run_millennium_bench.py
```
