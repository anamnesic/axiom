# P vs NP

- Registro: 17 de outubro de 2026.
- Situação matemática: **em aberto**, conforme a [página oficial do Clay](https://www.claymath.org/millennium/p-vs-np/).
- Situação da investigação: exemplo combinatório e ambiente avaliados; nenhuma
  demonstração de P = NP ou P ≠ NP fornecida ou produzida.
- Referência técnica: [descrição oficial por Stephen Cook](https://www.claymath.org/wp-content/uploads/2022/06/pvsnp.pdf).

## Descrição fornecida

> If it is easy to check that a solution to a problem is correct, is it also easy to solve the problem? This is the essence of the P vs NP question. Typical of the NP problems is that of the Hamiltonian Path Problem: given N cities to visit, how can one do this without visiting a city twice? If you give me a solution, I can easily check that it is correct. But I cannot so easily find a solution.

## Material já salvo

- [Relatório do exemplo e do ambiente](REPORT.md).
- [Evidências completas da execução](validation.json).
- [Script de reprodução](validate.py).

Esses arquivos registram uma execução anterior e suas limitações. Não constituem
uma solução do problema do Clay.

## Roteiro inicial de investigação

- [ ] Fixar as definições de linguagem, modelo de computação, P, NP e tempo
  polinomial a partir do enunciado oficial.
- [ ] Selecionar uma afirmação auxiliar ou algoritmo candidato concreto; separar
  correção, análise de tempo no pior caso e abrangência das entradas.
- [ ] Revalidar o ambiente AXIOM e registrar cada resultado com `guarantee`,
  `verification.passed` e comandos de reprodução. Tratar testes finitos como
  testes finitos; revisar a correspondência de qualquer formalização ao enunciado.

Aplicam-se as [orientações comuns de registro](../README.md#como-registrar-o-trabalho).
