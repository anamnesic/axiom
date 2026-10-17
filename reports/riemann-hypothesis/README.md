# Riemann Hypothesis — Hipótese de Riemann

Data do registro: 2026-10-17.

Status matemático: **em aberto**, conforme a [página oficial do Clay Mathematics Institute](https://www.claymath.org/millennium/riemann-hypothesis/), consultada na data do registro.

Status local: **validação empírica e analítica executada**. Todas as 24 checagens automatizadas de propriedades clássicas da função zeta de Riemann foram validadas no AXIOM v0.2.1. O relatório completo e evidências detalhadas encontram-se em:
- [Relatório Técnico de Validação (REPORT.md)](REPORT.md)
- [Evidências e Hashes de Auditoria (validation.json)](validation.json)
- [Script de Reprodução Automatizado (validate.py)](validate.py)

> [!IMPORTANT]
> Esta pasta documenta propriedades analíticas, especiais e controles negativos da função zeta de Riemann sob o AXIOM v0.2.1. **Não apresenta, não constitui e não alega uma demonstração da Hipótese de Riemann completa.**

## Descrição oficial do problema

> The prime number theorem determines the average distribution of the primes. The Riemann hypothesis tells us about the deviation from the average. Formulated in Riemann’s 1859 paper, it asserts that all the ‘non-obvious’ zeros of the zeta function are complex numbers with real part 1/2.

## Fonte oficial

- [Riemann Hypothesis — Clay Mathematics Institute](https://www.claymath.org/millennium/riemann-hypothesis/).
- [The Millennium Prize Problems — índice oficial](https://www.claymath.org/millennium-problems/).
- [Descrição técnica de Enrico Bombieri](https://www.claymath.org/wp-content/uploads/2022/05/riemann.pdf).

## Como reproduzir

Na raiz do repositório:

```powershell
python reports/riemann-hypothesis/validate.py
```
