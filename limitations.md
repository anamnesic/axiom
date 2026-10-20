# Limitações Técnicas, Formais e Teóricas — Chronokairo AXIOM

> **Versão:** v0.2.8  
> **Status:** Ativo & Auditado  
> **Compromisso:** Honestidade computacional e postura estritamente *fail-closed*.

Este documento explicita de forma transparente e cientificamente rigorosa os limites teóricos intrínsecos, as fronteiras computacionais e as restrições da implementação atual do **Chronokairo AXIOM (v0.2.8)**.

---

## 1. Limites Teóricos Fundamentais da Matemática e da Computação

Nenhum software de álgebra computacional ou assistente de prova formal pode transcender as barreiras indecidíveis da lógica matemática:

1. **Teorema de Richardson (1968)**:
   A equivalência de expressões analíticas com zero é **indecidível** para a classe de funções gerada por inteiros, $\pi$, $\ln(2)$, operações aritméticas elementares, funções trigonométricas ($\sin$), exponenciais ($\exp$) e a função valor absoluto ($|x|$).
   - *Postura do AXIOM*: O AXIOM não assume que duas expressões analíticas arbitrárias possam ter sua diferença simbolicamente reduzida a zero. Perante o Teorema de Richardson, o AXIOM combina simplificação canônica com amostragem numérica de multiprecisão (`mpmath`). Se a equivalência exata não for comprovada formalmente, o sistema rebaixa o resultado para `unverified` ou `numerical-approximation`, recusando a concessão de certificados indevidos de prova.
2. **Teoremas de Incompletude de Gödel (1931)**:
   Qualquer sistema formal consistente capaz de axiomatizar a aritmética elementar (como ZFC ou o Cálculo de Construções Indutivas do Lean 4) contém proposições verdadeiras que não podem ser demonstradas nem refutadas dentro do próprio sistema.
   - *Postura do AXIOM*: O AXIOM não pode demonstrar a consistência do seu próprio conjunto de axiomas nem garantir a resolução de conjecturas abertas arbitrárias formuladas no Lean 4.
3. **Indecidibilidade do Décimo Problema de Hilbert (Matiyasevich, 1970)**:
   Não existe algoritmo computacional geral para decidir se uma equação diofantina polinomial arbitrária possui raízes inteiras.
   - *Postura do AXIOM*: A ferramenta `math_solve` com hipóteses diofantinas (`assumptions={'x': 'integer'}`) atua estritamente sobre polinômios univariados, sistemas lineares, formas quadráticas e casos com algoritmos de terminação comprovada.

---

## 2. Limitações de Implementação e Dependências do Host

### 2.1. Dependência do Ambiente Local Lean 4 / Lake
- O motor de prova formal `LeanEngine` depende da presença dos executáveis `lean` e `lake` no ambiente do usuário (gerenciados via `elan`).
- **Comportamento quando ausente**: Se o Lean não estiver instalado no host, o AXIOM não interrompe a execução com exceções não-tratadas; ele sinaliza o resultado como `unverified` com detalhe explícito indicando que o kernel formal não pôde ser invocado no host local.

### 2.2. Isolamento de Processos e Sandbox do Lean 4
- Scripts Lean 4 não confiáveis são executados em diretórios temporários isolados (*scratch sandbox*) com variáveis de ambiente sanitizadas (`_build_sandboxed_env` remove tokens de API, chaves AWS/GitHub e credenciais do usuário), com limites de memória (`-M 2048`), cota de passos do elaborador (`-T 100000`) e timeout estrito.
- **Fronteira atual**: Esse isolamento opera no nível de processo da aplicação. Ele ainda não utiliza jaulas completas de contêiner ou namespaces do kernel do sistema operacional (como `bwrap` ou `cgroups` no Linux), que estão projetados para versões futuras.

### 2.3. Auditoria Formal de Declarações e Alinhamento de Especificação
- A extração de declarações Lean (`_extract_lean_declarations`) utiliza análise léxica com balanceamento de parênteses, chaves e colchetes para separar binders tipados `(n : Nat)`, binders implícitos `{α : Type}` e instâncias de classes `[CommRing α]`.
- **Fronteira atual**: Essa extração não executa o elaborador completo do compilador Lean para desvendar abreviações sintáticas ultra-complexas ou metaprogramas avançados. Coincidências léxicas com conjecturas canônicas externas geram no máximo o status `candidate` (`congruent=False`), exigindo comprovação formal ou simbólica para a promoção a `verified`.

### 2.4. Aritmética de Ponto Flutuante e Tolerâncias Numéricas
- Embora as verificações numéricas empreguem aritmética de precisão arbitrária (`mpmath`) com 35 a 50 dígitos decimais de trabalho, cálculos analíticos próximos de singularidades essenciais ou polos de alta ordem continuam sujeitos a cancelamento catastrófico.
- O AXIOM não promove aproximações numéricas a identidades exatas (`EXACT_SYMBOLIC`), mantendo-as na categoria `numerical-approximation` ou exigindo tolerância explícita do usuário.

### 2.5. Completude dos Conjuntos Solução
- Para equações polinomiais em uma variável sobre $\mathbb{C}$, a completude do conjunto solução é formalmente auditada via soma das ordens de multiplicidade comparadas ao grau algébrico total (Teorema Fundamental da Álgebra).
- Para equações transcendentes ou periódicas (e.g., $\sin(x) = 0$), os motores fornecem apenas uma amostra de soluções fundamentais e o AXIOM marca explicitamente `solution_complete = False` para alertar o agente sobre a existência de raízes infinitas adicionais.

### 2.6. Cálculo Tensorial e Geometria Diferencial
- O módulo `math_tensor` efetua diferenciação e contração simbólica rigorosa para tensores de curvatura (Christoffel, Riemann, Ricci, Einstein) em cartas de coordenadas locais fixadas.
- O sistema não executa análise topológica global (cálculo de grupos de homologia, invariantes de Donaldson/Seiberg-Witten ou cirurgias de fluxo de Ricci).

### 2.7. Sondas de Fronteira nos Problemas do Milênio
- As suítes de validação dos sete Problemas do Prêmio Clay do Milênio em `reports/` e no benchmark `run_millennium_bench.py` funcionam **estritamente como sondas de estresse epistêmico e controles negativos**.
- O AXIOM **não reivindica solução, avanço original ou resolução de nenhum problema aberto** (a Conjectura de Poincaré é verificada como resolvida pelo trabalho histórico de Grigori Perelman; Navier-Stokes valida a dissipação e energia clássica de Taylor-Green recusando qualquer certificação prematura de blowup ou regularidade global).

---

## 3. Resumo Ético e Epistemológico

O AXIOM foi construído sob um princípio inegociável de integridade científica:
> *Um sistema de IA que admite sua limitação com garantia `unverified` é infinitamente superior a um sistema que alucina uma demonstração falsa com falsa aparência de certeza.*
