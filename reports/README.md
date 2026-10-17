# Problemas do Milênio — Fila de Investigação AXIOM

Registrado em 17 de outubro de 2026 a pedido do usuário. Cada problema tem sua
própria pasta, com a descrição fornecida, fonte técnica e roteiro de investigação.

| Problema | Situação matemática | Situação neste projeto |
| --- | --- | --- |
| [Birch and Swinnerton-Dyer](birch-and-swinnerton-dyer/README.md) | Em aberto | Investigação planejada |
| [Conjectura de Hodge](hodge-conjecture/README.md) | Em aberto | Investigação planejada |
| [Navier-Stokes (Existência e Suavidade)](navier-stokes/README.md) | Em aberto | Formulação registrada; verificação de identidades e soluções exatas planejada |
| [P vs NP](p-vs-np/README.md) | Em aberto | Exemplo combinatório e ambiente avaliados ([REPORT.md](p-vs-np/REPORT.md)) |
| [Hipótese de Riemann](riemann-hypothesis/README.md) | Em aberto | Propriedades analíticas e controles validados ([REPORT.md](riemann-hypothesis/REPORT.md)) |
| [Yang-Mills e o Gap de Massa](yang-mills-mass-gap/README.md) | Em aberto | Investigação planejada |
| [Conjectura de Poincaré](poincare-conjecture/README.md) | Resolvido (G. Perelman) | Estudo da demonstração e reprodução de resultados auxiliares planejados |

Situações matemáticas conferidas na [lista oficial do Clay Mathematics Institute](https://www.claymath.org/millennium-problems/).
Este índice reúne a totalidade dos **sete Problemas do Prêmio do Milênio** do Clay Mathematics Institute.
A criação das pastas registra a fila de trabalho e infraestrutura de validação; não constitui demonstração matemática dos problemas abertos.

## Como registrar o trabalho

1. Ler o enunciado técnico oficial e fixar hipóteses, definições e um objetivo
   restrito antes de iniciar cada tentativa.
2. Registrar tentativas, inclusive falhas e contraexemplos, na pasta do problema,
   com data, fontes, método, código e comandos de reprodução.
3. Salvar os resultados AXIOM completos em JSON e inspecionar sempre `guarantee`
   e `verification.passed`. A execução de um comando não equivale à validação
   matemática da afirmação.
4. Distinguir observações numéricas, casos particulares, lemas e demonstração
   geral. Para uma prova formal, conferir também o enunciado efetivamente provado,
   as hipóteses e as dependências axiomáticas.

Os resumos em inglês foram fornecidos pelo usuário e preservados nas respectivas
pastas. São descrições introdutórias; os enunciados técnicos oficiais devem orientar
a investigação. O diagnóstico anterior de ferramentas está no
[relatório de P vs NP](p-vs-np/REPORT.md); revalidar o ambiente antes de novos trabalhos.
