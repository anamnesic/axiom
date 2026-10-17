# Problemas do Milênio — Fila de Investigação e Validação AXIOM

Registrado em 17 de outubro de 2026 a pedido do usuário. Cada problema possui sua
própria pasta de pesquisa reprodutível com formulação matemática formal, suíte de verificação
autônoma (`validate.py`), evidências integrais serializadas (`validation.json`) e relatório
detalhado com controles negativos (`REPORT.md`).

| Problema | Situação matemática | Situação no AXIOM v0.2.3 | Critérios & Fail-Closed |
| --- | --- | --- | --- |
| [Birch and Swinnerton-Dyer](birch-and-swinnerton-dyer/README.md) | Em aberto | Propriedades analíticas e controles validados ([REPORT.md](birch-and-swinnerton-dyer/REPORT.md)) | 15/15 checks (100% fail-closed) |
| [Conjectura de Hodge](hodge-conjecture/README.md) | Em aberto | Propriedades analíticas e controles validados ([REPORT.md](hodge-conjecture/REPORT.md)) | 11/11 checks (100% fail-closed) |
| [Navier-Stokes (Existência e Suavidade)](navier-stokes/README.md) | Em aberto | Soluções exatas e dissipação dinâmica validadas ([REPORT.md](navier-stokes/REPORT.md)) | 16/16 checks (100% fail-closed) |
| [P vs NP](p-vs-np/README.md) | Em aberto | Exemplo combinatório e controles validados ([REPORT.md](p-vs-np/REPORT.md)) | 12/12 checks (100% fail-closed) |
| [Hipótese de Riemann](riemann-hypothesis/README.md) | Em aberto | Propriedades analíticas e linha crítica validadas ([REPORT.md](riemann-hypothesis/REPORT.md)) | 24/24 checks (100% fail-closed) |
| [Yang-Mills e o Gap de Massa](yang-mills-mass-gap/README.md) | Em aberto | Álgebra de gauge e instantons validados ([REPORT.md](yang-mills-mass-gap/REPORT.md)) | 12/12 checks (100% fail-closed) |
| [Conjectura de Poincaré](poincare-conjecture/README.md) | Resolvido (G. Perelman) | Geometria de $S^3$ e fluxo de Ricci validados ([REPORT.md](poincare-conjecture/REPORT.md)) | 12/12 checks (100% fail-closed) |

Situações matemáticas conferidas na [lista oficial do Clay Mathematics Institute](https://www.claymath.org/millennium-problems/).  
Este índice reúne a totalidade dos **sete Problemas do Prêmio do Milênio** do Clay Mathematics Institute.  
**Taxa Global de Falsos Positivos nos 7 Problemas:** **0.0%** (0 falsos positivos em 102 critérios de avaliação dinâmica).  
A validação de propriedades auxiliares e controles negativos **não constitui demonstração matemática dos problemas abertos**, reafirmando a integridade científica do projeto.

## Como registrar o trabalho e reproduzir

Para reproduzir a suíte completa de qualquer um dos problemas a partir da raiz do repositório:

```powershell
python reports/birch-and-swinnerton-dyer/validate.py
python reports/hodge-conjecture/validate.py
python reports/navier-stokes/validate.py
python reports/p-vs-np/validate.py
python reports/poincare-conjecture/validate.py
python reports/riemann-hypothesis/validate.py
python reports/yang-mills-mass-gap/validate.py
```

### Regras Metodológicas Obrigatórias

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
