# Limitações Técnicas e Teóricas — Chronokairo AXIOM

Este documento explicita de forma honesta, transparente e cientificamente rigorosa os limites teóricos intrínsecos, as fronteiras computacionais e as restrições da implementação atual do **Chronokairo AXIOM (v0.2.1)**.

---

## 1. Limites Teóricos Fundamentais da Matemática e da Computação

Nenhum software de álgebra computacional ou provador de teoremas pode transcender as barreiras formais da decidibilidade matemática:

1. **Teorema de Richardson (1968)**:
   A equivalência de expressões analíticas com zero é **indecidível** para a classe de funções gerada por inteiros, $\pi$, $\ln(2)$, adições, multiplicações, composições de funções trigonométricas ($\sin$), exponenciais ($\exp$) e a função valor absoluto ($|x|$).
   - *Impacto no AXIOM*: O AXIOM não garante que todo par de expressões equivalentes terá sua diferença simbólica reduzida a zero. Perante o Teorema de Richardson, o AXIOM recorre à amostragem numérica de multiprecisão (`mpmath`). Se a amostragem for insuficiente para provar a identidade, o sistema rebaixa a garantia para `unverified` ou `numerical-approximation`, mantendo postura fail-closed.
2. **Teoremas de Incompletude de Gödel (1931)**:
   Qualquer sistema formal consistente capaz de expressar a aritmética elementar (como ZFC ou a Teoria dos Tipos Dependentes do Lean 4) contém sentenças verdadeiras que não podem ser demonstradas dentro do próprio sistema.
   - *Impacto no AXIOM*: O AXIOM não pode demonstrar a consistência do seu próprio conjunto de axiomas nem resolver todas as conjecturas matemáticas formuladas em Lean 4.
3. **Indecidibilidade do Décimo Problema de Hilbert (Matiyasevich, 1970)**:
   Não existe algoritmo geral para decidir se uma equação diofantina polinomial arbitrária possui soluções inteiras.
   - *Impacto no AXIOM*: A ferramenta `math_solve` com hipóteses de inteiros (`assumptions={'x': 'integer'}`) tem escopo restrito a equações lineares, quadráticas e sistemas solúveis via algoritmos específicos de bases de Gröbner e fatoração.

---

## 2. Limitações de Implementação e Dependências do Host

### 2.1. Dependência do Ambiente Local Lean 4 / Lake
- O motor de prova formal `LeanEngine` depende da presença do executável `lake` e do compilador `lean` no ambiente do usuário (disponíveis via `~/.elan/bin` ou `PATH`).
- **Comportamento quando ausente**: Se o Lean não estiver instalado no host, o AXIOM não quebra nem gera exceções não-tratadas; ele reporta status `unverified` com detalhe explícito indicando que o kernel formal não pôde ser executado localmente.

### 2.2. Aritmética de Ponto Flutuante e Tolerâncias Numéricas
- Embora a conferência numérica utilize aritmética de multiprecisão arbitrária (`mpmath`) com 35 a 50 dígitos decimais de precisão de trabalho, avaliações numéricas estão sujeitas a cancelamento catastrófico em proximidade extrema de polos de ordem elevada ou oscilações de frequência infinita (e.g., $\sin(1/x)$ quando $x \to 0$).
- Tolerâncias padrão adotadas ($\varepsilon = 10^{-4}$ a $10^{-8}$) são projetadas para distinguir identidades de desvios grosseiros, mas podem requerer ajustes em problemas com escalas físicas extremas.

### 2.3. Equações Transcendentes e Completude de Conjuntos Solução
- Para equações algébricas polinomiais, o campo `solution_complete` é garantido como `true` pelo Teorema Fundamental da Álgebra.
- Para equações transcendentes (e.g. $\sin(x) = 0$, $x e^x = 1$), os motores retornam amostras de raízes principais acompanhadas da representação do conjunto de imagens periódicas (`ImageSet`). O AXIOM marca `solution_complete = false` para alertar o agente de que existem infinitas raízes adicionais.

### 2.4. Limites de Cobertura do Cálculo Tensorial
- O módulo `axiom.tensor` calcula quantidades de geometria diferencial (Christoffel, Riemann, Ricci, Einstein) para métricas locais especificadas analiticamente em cartas de coordenadas fixas.
- Ele não realiza análise topológica global (como cálculo de invariantes de homologia, números de Betti ou fluxo de Ricci com cirurgia) nem resolve equações de campo de Einstein de valor inicial sem hipóteses de simetria (como Birkhoff).

### 2.5. Allowlist do Parser AST
- Por razões de segurança e sandbox para agentes autônomos, o `Parser` bloqueia qualquer chamada que utilize `eval`, `exec`, acesso a atributos privados `__class__`, imports dinâmicos ou lambdas.
- Expressões matemáticas que dependem de construções imperativas de programação em Python devem ser normalizadas para funções matemáticas puras.

---

## 3. Resumo Ético e Epistemológico

O AXIOM foi desenhado sob o lema da **honestidade computacional**:
> *Um sistema que admite sua limitação com garantia `unverified` é infinitamente superior a um sistema que alucina uma demonstração falsa com aparência de certeza.*
