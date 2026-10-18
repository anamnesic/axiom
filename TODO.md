# Auditoria de gaps — Chronokairo AXIOM v0.2.5

Revisei o estado atual do repositório [chronokairo/axiom](https://github.com/chronokairo/axiom?utm_source=chatgpt.com), no commit `66307c38b67a`, incluindo o núcleo matemático, o sistema de provas, sessões, benchmarks e a estrutura do projeto.

O CI principal está aprovado, com 8/8 jobs, e o Millennium Bench registra 105/105 critérios. Isso demonstra que os testes existentes passaram, mas não garante a ausência de defeitos fora dos casos testados.

Minha conclusão principal: antes de ampliar as funcionalidades, você precisa fortalecer a integridade dos certificados matemáticos e das evidências de pesquisa.

## P0 — Gaps críticos para corrigir agora

| ID    | Gap encontrado                                                                                                            | Correção necessária                                                         |
| ----- | ------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| P0-01 | Enunciados matemáticos genéricos ainda podem ser considerados `verified` apenas por coincidência lexical.                 | Nunca promover palavras-chave a equivalência demonstrada.                   |
| P0-02 | O parser próprio de declarações Lean, baseado em regex, não representa corretamente toda a sintaxe e os tipos elaborados. | Usar a representação elaborada pelo Lean para auditar proposições.          |
| P0-03 | Sessões carregadas de JSON podem declarar garantias sem reexecutar as respectivas verificações.                           | Tratar evidências importadas como não confiáveis até serem revalidadas.     |
| P0-04 | `chain_guarantee` combina níveis declarados das etapas, sem comprovar que a conclusão de uma etapa fundamenta a próxima.  | Separar a qualidade individual dos resultados da validade lógica da cadeia. |

### P0-01 — O exemplo de Goldbach continua relevante

Um teorema elementar chamado `goldbach_add_zero`, acompanhado de `canonical_statement="Goldbach conjecture"`, pode ser classificado como congruente pelo auditor genérico.

Isso é perigoso porque a validade do teorema dentro do Lean não estabelece sua equivalência com a conjectura externa.

Critério de correção: nenhuma conjectura pode receber certificação canônica sem uma evidência independente da equivalência entre os enunciados.

### P0-03 — Novo problema identificado nas sessões

Em `src/axiom/session.py`, `ResearchSession.load()` aceita entradas JSON armazenadas e `chain_guarantee` confia no campo `guarantee` de cada entrada.

Uma sessão importada contendo:

```json
{
  "name": "research",
  "entries": [
    {
      "ok": true,
      "guarantee": "formal-proof"
    }
  ]
}
```

pode calcular `chain_guarantee = formal-proof`, embora nenhuma prova Lean tenha sido reexecutada ou validada nessa importação. É um defeito no modelo de confiança da evidência, não uma demonstração de execução remota ou acesso indevido.

A correção é introduzir proveniência verificável e revalidação de resultados importados.

## P1 — Segurança e integridade operacional

O AXIOM é executado por agentes de IA com acesso a ferramentas locais. Por isso, a superfície de segurança é maior que a de uma biblioteca matemática convencional.

| ID    | Gap                                                                                                      | Solução recomendada                                                                                              |
| ----- | -------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| P1-01 | O motor Lean compila código fornecido pelo chamador usando subprocessos locais.                          | Isolar a execução em um processo ou contêiner sem privilégios, com limites de CPU, memória, tempo, disco e rede. |
| P1-02 | `math_verify` aceita caminhos locais para arquivos JSON.                                                 | Restringir caminhos acessíveis pelo MCP ou exigir autorização explícita para leitura de arquivos.                |
| P1-03 | `math_plot` aceita um caminho de saída fornecido pelo chamador.                                          | Limitar gravações a uma pasta autorizada e evitar sobrescritas inesperadas.                                      |
| P1-04 | Os adaptadores externos dependem de executáveis instalados no host.                                      | Registrar versão, hash do executável, ambiente e condições de execução.                                          |
| P1-05 | Não há uma política uniforme de orçamento de recursos para todas as operações matemáticas.               | Adicionar limites de expressão, complexidade, duração e memória por ferramenta.                                  |
| P1-06 | O contrato `MathResult` exige `Verification(passed=True)`, mas não autentica a origem dessa verificação. | Diferenciar evidência calculada nesta execução, evidência importada e evidência revalidada.                      |

O P1-01 merece atenção especial: verificar uma prova Lean não significa executar o código de entrada em um ambiente isolado. O Lean possui mecanismos de metaprogramação que tornam inadequado executar fontes não confiáveis com os mesmos privilégios do usuário.

Para um MCP utilizado autonomamente por agentes, eu trataria esse endurecimento como requisito de lançamento.

## P1 — Solidez matemática e provas formais

| ID    | Gap                                                                                                                   | O que implementar                                                                                         |
| ----- | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| P1-07 | Auditoria das hipóteses Lean por regex e comparação de strings.                                                       | Extrair binders, tipos, hipóteses implícitas e instâncias de classes a partir do ambiente Lean elaborado. |
| P1-08 | `candidate` e `scoped` ainda podem apresentar `is_aligned=True`.                                                      | Separar associação temática, compatibilidade de escopo e equivalência formal em campos distintos.         |
| P1-09 | Quando não há referência canônica, o auditor retorna `unreviewed` acompanhado de `congruent=True`.                    | Representar congruência desconhecida como `null` ou `not_applicable`, não como verdadeira.                |
| P1-10 | A detecção de tautologias é principalmente sintática.                                                                 | Detectar o que a proposição realmente afirma, sem depender do nome do teorema ou da presença de `rfl`.    |
| P1-11 | `FORMAL_PROOF` para um lema e certificação de uma conjectura externa ainda compartilham conceitos no contrato.        | Criar `kernel_proof_valid` e `canonical_claim_certified` como resultados independentes.                   |
| P1-12 | A verificação por substituição confirma raízes apresentadas, não sua completude.                                      | Exigir certificado separado de completude do conjunto solução.                                            |
| P1-13 | A completude de soluções polinomiais aparece na documentação como consequência do Teorema Fundamental da Álgebra.     | Comprovar que o algoritmo retornou todas as raízes, incluindo multiplicidades e domínio escolhido.        |
| P1-14 | Revalidação de JSON cobre apenas parte das operações.                                                                 | Estender `axiom verify` a sistemas, matrizes, EDOs, tensores e outros resultados estruturados.            |
| P1-15 | A revalidação de integrais trata o resultado JSON como antiderivada, sem recuperar limites de integração.             | Diferenciar explicitamente integrais definidas e indefinidas.                                             |
| P1-16 | Verificações simbólicas e numéricas não oferecem certificados uniformes de domínio, precisão e condições de validade. | Padronizar `domain`, `assumptions`, `precision`, `tolerance`, `error_bound` e `proof_obligations`.        |
| P1-17 | O campo `verified` pode ser verdadeiro para um estado operacional, como visualização ou consulta de catálogo.         | Fornecer `mathematically_verified` separado de `operation_succeeded`.                                     |

Dois exemplos de testes que recomendo transformar em regressões obrigatórias:

Teste 1 — Extração de teoremas

```python
source = "theorem add_zero (n : Nat) : n + 0 = n := by rfl"
decls = _extract_lean_declarations(source)
assert len(decls) == 1
assert decls[0]["prop"] == "n + 0 = n"
```

Reproduzi isoladamente a regex atual: ela retorna zero declarações nesse exemplo.

Teste 2 — Proibição de certificação por nome

```python
res = ax.prove(
    "theorem goldbach_add_zero (n : Nat) : n + 0 = n := by rfl",
    canonical_statement="Goldbach conjecture",
    declared_hypotheses=["n : Nat"],
)
manifest = res.verification.data["formal_manifest"]
assert manifest["spec_alignment"]["congruent"] is False
```

Comportamento exigido após correção: o nome do teorema não pode comprovar correspondência semântica.

Uma distinção importante: o problema com integrais definidas em JSON é verificável no código. `_verify_dict_payload()` chama `verify_integral()` sem recuperar `lower` e `upper`, embora esses limites sejam necessários para validar o resultado de uma integral definida.

## P1 — Benchmarks, CI e confiabilidade experimental

| ID    | Gap                                                                                                                                 | O que corrigir                                                                                        |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| P1-18 | Métricas como `fail_closed_rate` e `true_positive_rate` podem assumir 100% quando não há amostras.                                  | Retornar `null` ou `N/A` quando o denominador for zero.                                               |
| P1-19 | O runner aceita métricas declaradas pelos próprios validadores.                                                                     | Recalcular contagens a partir dos casos individuais e rejeitar inconsistências.                       |
| P1-20 | Alguns testes negativos aceitam tanto `disproven` quanto `inconclusive`.                                                            | Medir separadamente refutações, recusas de certificação e resultados inconclusivos.                   |
| P1-21 | Parte dos controles Lean pode passar mesmo sem o kernel instalado.                                                                  | Separar testes de classificação semântica de testes que exigem execução real do Lean.                 |
| P1-22 | Os 105 critérios são casos internos e conhecidos antecipadamente.                                                                   | Criar conjuntos adversariais independentes, testes gerados e casos não utilizados no desenvolvimento. |
| P1-23 | Não existe cobertura sistemática de testes por propriedade e mutação.                                                               | Adicionar Hypothesis, testes diferenciais e mutation testing.                                         |
| P1-24 | Não há critérios obrigatórios de regressão de desempenho.                                                                           | Estabelecer limites de latência, memória e tamanho de expressão.                                      |
| P1-25 | As versões das dependências matemáticas não estão fixadas para todos os experimentos.                                               | Usar ambiente reproduzível, hashes e manifestos de execução.                                          |
| P1-26 | O CI não possui etapas dedicadas de auditoria de dependências e análise de segurança.                                               | Adicionar auditoria de dependências, análise estática e verificação de segredos.                      |
| P1-27 | As chamadas MCP não apresentam um contrato uniforme de limites de entrada e saída.                                                  | Validar rigorosamente argumentos e limites de recursos antes do despacho.                             |
| P1-28 | O resultado `MathResult` pode ser modificado depois de sua construção, enfraquecendo as invariantes verificadas em `__post_init__`. | Tornar os resultados imutáveis ou revalidar as invariantes antes de serializar e exportar.            |

Um detalhe científico importante: zero falsos positivos nos 38 controles atuais não permite afirmar taxa de falsos positivos zero para entradas arbitrárias. A documentação deve apresentar a taxa observada, o conjunto testado e a incerteza estatística.

## P2 — Gaps científicos e de funcionalidades

| ID    | Gap                                                                                                                         | Entrega recomendada                                                                                     |
| ----- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| P2-01 | Validação cruzada automática SymPy × SageMath × Julia não concluída.                                                        | Runner multiengine com comparação normalizada e relatório de divergências.                              |
| P2-02 | A integração formal testada no CI usa um workspace Lean mínimo, sem dependência Mathlib declarada.                          | Acrescentar um projeto Mathlib real e testes de lemas importados.                                       |
| P2-03 | A ferramenta de busca Mathlib não garante que um teorema encontrado esteja disponível ou que sua assinatura continue igual. | Verificar módulo, versão e tipo da declaração no ambiente instalado.                                    |
| P2-04 | A validação de Navier–Stokes ainda usa expressões predefinidas para parte do balanço de momento e pressão.                  | Derivar todos os termos da EDP a partir dos campos \(u,v,p\), nas duas componentes.                   |
| P2-05 | O exemplo Lean de Navier–Stokes é um controle de metadados, não uma formalização da EDP.                                    | Criar uma especificação formal genuína de campos, condições iniciais, regularidade, domínio e equações. |
| P2-06 | Não há um fluxo geral de resolução ou simulação de EDPs.                                                                    | Definir interface de EDP, condições de contorno, discretização, erro e estabilidade.                    |
| P2-07 | Falta certificação rigorosa para resultados numéricos delicados.                                                            | Introduzir aritmética intervalar, cotas de erro e distinção entre aproximação e intervalo garantido.    |
| P2-08 | Exploração de conjecturas não gera automaticamente obrigações formais de prova.                                             | Criar um ciclo `conjecture → counterexample → lemma → proof obligation → certificate`.                  |
| P2-09 | Não existe comparação sistemática entre agentes LLM com e sem AXIOM.                                                        | Benchmark de agentes com tarefas cegas, baselines, taxa de erro, custo e latência.                      |
| P2-10 | Sessões exportam histórico, mas não dependências lógicas estruturadas entre passos.                                         | Criar um grafo de demonstração com premissas, conclusões e referências de certificados.                 |
| P2-11 | O suporte de revalidação JSON não cobre todos os 21 tipos de ferramentas MCP.                                               | Estabelecer esquema de revalidação por operação, quando matematicamente aplicável.                      |
| P2-12 | Resultados científicos carecem de um identificador estável de execução e integridade dos artefatos.                         | Registrar hash de entrada, código, ambiente, resultados e dependências.                                 |

### O principal gap para Navier–Stokes

Hoje você já deriva a energia de uma solução bidimensional conhecida. Isso é valioso para validar a infraestrutura.

Mas o problema de regularidade global em 3D exige objetos e propriedades muito mais gerais:

- Campo de velocidade tridimensional e pressão.
- Incompressibilidade e equações de momento.
- Condições iniciais e domínio espacial definidos rigorosamente.
- Espaços funcionais, normas e hipóteses de regularidade.
- Lemas de estimativas de energia e existência local.
- Formulação de existência global ou formação de singularidade sob as condições exatas do problema.

O próximo avanço científico do AXIOM seria formalizar e testar lemas existentes e bem estabelecidos nessas áreas, antes de buscar um resultado original sobre o problema aberto.

## P2 — Documentação, produto e open source

| ID    | Gap                                                                                                                   | Ação                                                                                                     |
| ----- | --------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| P2-13 | `docs/use-cases.md` não existe.                                                                                       | Documentar os dez casos de uso com comandos, entradas, saídas e garantias esperadas.                     |
| P2-14 | O README possui informações históricas desatualizadas, como a contagem de critérios em sua árvore de arquivos.        | Gerar indicadores atuais automaticamente no CI.                                                          |
| P2-15 | `limitations.md` ainda se identifica como v0.2.1.                                                                     | Atualizar para v0.2.5, especialmente limites da auditoria formal.                                        |
| P2-16 | A documentação pode sugerir que todos os motores matemáticos estão igualmente completos.                              | Criar matriz de suporte por operação, engine, plataforma e tipo de garantia.                             |
| P2-17 | Não há release publicado ou tag de versão identificado na consulta atual.                                             | Preparar release versionado, changelog e artefatos distribuíveis.                                        |
| P2-18 | O build gera wheel e sdist, mas não há teste explícito da instalação desses artefatos em ambiente limpo.              | Executar smoke tests a partir dos pacotes construídos.                                                   |
| P2-19 | O `scorecard.json` versionado contém informações específicas do host que executou o benchmark.                        | Normalizar caminhos e separar artefatos locais de resultados publicados.                                 |
| P2-20 | Não há política pública de divulgação de vulnerabilidades identificada na árvore do repositório.                      | Adicionar `SECURITY.md`, escopo de suporte e processo de reporte.                                        |
| P2-21 | Não há guia de contribuição específico identificado na árvore.                                                        | Criar `CONTRIBUTING.md` com regras para novos verificadores, testes adversariais e mudanças de garantia. |
| P2-22 | A descrição do pacote e os exemplos científicos ainda não demonstram de ponta a ponta todos os benefícios anunciados. | Publicar demos reproduzíveis para agentes, cálculo simbólico, Lean e pesquisa matemática.                |

## Ordem de execução recomendada

### Fase 1 — Integridade dos certificados (Bloqueante)
Corrigir P0-01 a P0-04. Nenhum texto ou identificador deve produzir certificado de equivalência; nenhuma sessão importada deve criar uma garantia formal sem revalidação.

### Fase 2 — Segurança do MCP (Antes de agentes autônomos)
Endurecer a execução Lean e operações de arquivo; adicionar limites de recursos e validação de argumentos.

### Fase 3 — Confiabilidade matemática (Próxima versão)
Corrigir auditoria de hipóteses, completude de soluções, revalidação JSON e semântica de `verified`.

### Fase 4 — Qualidade experimental (Antes de publicação científica)
Introduzir testes adversariais independentes, métricas reproduzíveis, controles com Lean real e comparações entre motores.

### Fase 5 — Expansão científica (v0.3.0+)
Formalização Lean/Mathlib de resultados conhecidos, exploração matemática estruturada, EDPs e estudos comparativos com agentes de IA.

## Critérios mínimos para considerar a próxima versão confiável

Checklist de aceite (10/10 concluídos):
- [x] Nenhuma correspondência lexical gera `verified` por conta própria.
- [x] A auditoria reconhece corretamente as assinaturas Lean usadas nos testes.
- [x] Resultados importados não recebem `formal-proof` sem revalidação.
- [x] A validade de cada passo e da cadeia de dependências são tratadas separadamente.
- [x] Execução de Lean não confiável ocorre em isolamento com limites de recursos.
- [x] Operações MCP de arquivos respeitam pastas e permissões autorizadas.
- [x] O CI executa os novos testes adversariais sem mocks no percurso crítico.
- [x] Benchmarks rejeitam métricas inconsistentes e saídas ausentes.
- [x] A documentação diferencia prova, aproximação, refutação e inconclusão.
- [x] Casos de uso demonstram comandos efetivos e garantias verificadas.

## Conclusão

A auditoria identificou 43 gaps, entre defeitos confirmados, riscos arquiteturais e capacidades ainda não implementadas. Não significa que existam 43 bugs: vários são requisitos de pesquisa ou de maturidade do produto. É uma lista abrangente do que foi possível identificar pela leitura estática do HEAD e pelas evidências públicas do CI, não uma garantia de completude absoluta.

Minha recomendação para o AXIOM é não expandir agora para novos problemas matemáticos. Primeiro feche os bloqueadores de integridade de certificados, proveniência e segurança. Depois fortaleça o rigor experimental e só então amplie a pesquisa com Lean e Mathlib.

Os arquivos mais importantes para começar são [core.py](https://github.com/chronokairo/axiom/blob/66307c38/src/axiom/core.py?utm_source=chatgpt.com), [session.py](https://github.com/chronokairo/axiom/blob/66307c38/src/axiom/session.py?utm_source=chatgpt.com), [lean_engine.py](https://github.com/chronokairo/axiom/blob/66307c38/src/axiom/engines/lean_engine.py?utm_source=chatgpt.com), [verification.py](https://github.com/chronokairo/axiom/blob/66307c38/src/axiom/verification.py?utm_source=chatgpt.com) e [run_millennium_bench.py](https://github.com/chronokairo/axiom/blob/66307c38/benchmarks/millennium/run_millennium_bench.py?utm_source=chatgpt.com).
