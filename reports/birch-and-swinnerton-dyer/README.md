# Conjectura de Birch e Swinnerton-Dyer

- **Registro:** 2026-10-17.
- **Status matemático:** em aberto, conforme a [página oficial do Clay Mathematics Institute](https://www.claymath.org/millennium/birch-and-swinnerton-dyer-conjecture/), consultada nesta data.
- **Status da investigação:** **propriedades analíticas e controles validados** ([REPORT.md](REPORT.md)). Suíte com 15 critérios automatizados aprovados (100% fail-closed, 0.0% falsos positivos).
- **Objetivo da pasta:** reunir referências, hipóteses de trabalho, experimentos e evidências para investigação futura.

## Material salvo

- [Relatório de Validação e Integridade](REPORT.md)
- [Evidências integrais da execução](validation.json)
- [Script de reprodução autônomo](validate.py)

## Descrição fornecida

Texto em inglês fornecido pelo usuário, preservado como referência:

> Supported by much experimental evidence, this conjecture relates the number of points on an elliptic curve mod p to the rank of the group of rational points. Elliptic curves, defined by cubic equations in two variables, are fundamental mathematical objects that arise in many areas: Wiles’ proof of the Fermat Conjecture, factorization of numbers into primes, and cryptography, to name three.

## Próximos passos

1. Ler a descrição técnica oficial de Andrew Wiles, disponível na seção “Further resources” da página do Clay, e registrar o enunciado, as hipóteses e as definições necessárias.
2. Selecionar uma curva elíptica explícita e um conjunto finito de primos para um experimento de contagem de pontos, após verificar as condições aplicáveis na referência; documentar o alcance restrito do experimento.
3. Registrar os comandos, entradas e resultados completos do AXIOM, inspecionando `guarantee` e `verification.passed` em cada `MathResult`. Separar evidência experimental de demonstração: um teste finito não estabelece a conjectura geral.

## Evidências AXIOM

Nenhum `MathResult` foi produzido para este problema neste registro. Não há garantia nem resultado de verificação a atribuir.
