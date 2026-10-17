# ADR-0013: Integridade dos Benchmarks Científicos, Métricas Derivadas e Taxonomia Epistemológica de Testes

- **Status**: Aceito (Accepted)
- **Data**: 2026-10-17
- **Versão do AXIOM**: v0.2.3

---

## Contexto

Na revisão por pares da versão v0.2.2 do Chronokairo AXIOM, foram identificados quatro pontos fundamentais para a credibilidade científica da infraestrutura de pesquisa e verificação:

1. **Métricas Estáticas vs. Dinâmicas**: Nos relatórios de validação dos Problemas do Milênio e no runner do benchmark consolidado (`run_millennium_bench.py`), métricas como `fail_closed_rate` e `false_positive_rate` vinham sendo atribuídas como constantes (`1.0` e `0.0`), em vez de serem derivadas dinamicamente da contagem e classificação individual dos testes (`kind`, `expected_verdict`, `observed_verdict`).
2. **Erro Físico-Matemático na Energia Cinética de Navier-Stokes**: No Vórtice de Taylor-Green bidimensional periódico, a integral da energia cinética total foi calculada como $E(t) = \frac{\pi^2}{2} e^{-4\nu t}$, quando a integração exata sobre o toro $[0, 2\pi]^2$ resulta em $E(t) = \pi^2 e^{-4\nu t}$. Correspondentemente, a taxa de decaimento temporal e a dissipação viscosa são $\frac{dE}{dt} = -4\nu \pi^2 e^{-4\nu t}$ e $D(t) = 4\nu \pi^2 e^{-4\nu t}$ (não $-2\nu \pi^2$). Esse erro numérico permaneceu oculto porque o teste comparava expressões com cancelamento prévio simplificado $(-2c + 2c == 0)$.
3. **Confusão Epistemológica entre Refutação e Sondas de Problemas Abertos**: Sondas de fronteira com variáveis livres (tais como `Delta_YM == 0` ou `hodge_class == algebraic_cycle`) eram classificadas genericamente como "refutações adversariais", porque o CAS encontra contraexemplos numéricos para variáveis escalares livres em $\mathbb{R}$. Contudo, o AXIOM não refutou nem provou os problemas em aberto subjacentes: ele apenas demonstrou que símbolos livres não satisfazem igualdade incondicional sem formalização teórica de operadores ou classes geométricas.
4. **Ausência do Millennium Research Bench no CI**: O benchmark consolidado dos Problemas do Milênio não estava integrado aos pipelines automatizados do GitHub Actions, impedindo a emissão de evidências contínuas em múltiplos sistemas operacionais.

---

## Decisões de Arquitetura

### 1. Taxonomia Epistemológica Ternária de Casos de Teste
Cada teste nos relatórios dos Problemas do Milênio passa a ser estruturado com os seguintes metadados explícitos:
- `id`: Identificador único do teste;
- `kind`: Categoria epistemológica:
  - `positive_claim`: Teorema, identidade exata ou valor analítico conhecido a ser demonstrado;
  - `negative_control`: Alegação matemática falsa que deve ser ativamente refutada com contraexemplo (`disproven`) ou conjunto vazio de soluções (`unsolved`);
  - `open_boundary_probe`: Prova de fronteira sobre problema aberto ou símbolo livre não-formalizado, onde o motor deve recusar prova (`fail-closed`), preservando a honestidade epistemológica sem pretensão de refutação do teorema físico/geométrico;
  - `operational_check`: Autoteste de integridade do ambiente (`doctor`);
- `expected_verdict`: Veredito esperado (`proven`, `disproven`, `unsolved`, `ok`);
- `observed_verdict`: Veredito observado retornado pelo motor;
- `evidence_type`: Tipo de garantia ou método de evidência;
- `is_false_positive`: Indicador booleano estrito ativado se um `negative_control` ou `open_boundary_probe` receber indevidamente veredito `proven` com `verification.passed = True`;
- `is_fail_closed`: Indicador booleano estrito ativado se nenhuma garantia matemática indevida for outorgada.

### 2. Eliminação de Métricas Estáticas e Cálculo Dinâmico Global
Todas as taxas passam a ser calculadas dinamicamente:
$$\text{False Positive Rate} = \frac{\sum \text{is\_false\_positive}}{\sum \text{Controles Negativos e Sondas de Fronteira}}$$
$$\text{Fail-Closed Rate} = \frac{\sum \text{is\_fail\_closed}}{\sum \text{Controles Negativos e Sondas de Fronteira}}$$
$$\text{True Positive Rate} = \frac{\sum \text{Verdadeiros Positivos}}{\sum \text{Afirmações Positivas}}$$

Se qualquer controle negativo ou sonda for aceito indevidamente como provado, a taxa de falsos positivos torna-se estritamente maior que zero e a suíte falha com código de saída 1. Falhas de sintaxe e exceções (`ok: false`) são registradas como `error` e não são mascaradas como contraexemplos matemáticos.

### 3. Derivação Simbólica Dinâmica da Energia no Vórtice de Taylor-Green
A validação de Navier-Stokes deixa de comparar identidades com cancelamento estático. O script `reports/navier-stokes/validate.py` executa a integração definida simbólica passo a passo:
1. $\int_0^{2\pi} \sin^2(x) dx = \pi$ (integrado via FTC com resíduo $< 10^{-16}$);
2. $\int_0^{2\pi} \cos^2(y) dy = \pi$ (integrado via FTC);
3. Por separação de variáveis, $\int_\Omega (u^2 + v^2) dx dy = 2\pi^2 e^{-4\nu t}$;
4. $E(t) = \frac{1}{2} \int_\Omega (u^2 + v^2) dx dy = \pi^2 e^{-4\nu t}$;
5. Diferenciação temporal $\frac{dE}{dt} = \frac{d}{dt}(\pi^2 e^{-4\nu t}) = -4\nu \pi^2 e^{-4\nu t}$;
6. Dissipação viscosa $D(t) = \nu \int_\Omega |\nabla \mathbf{u}|^2 dx dy = 4\nu \pi^2 e^{-4\nu t}$;
7. Balanço exato $\frac{dE}{dt} + D(t) = -4\nu \pi^2 e^{-4\nu t} + 4\nu \pi^2 e^{-4\nu t} \equiv 0$.

### 4. Integração Contínua no GitHub Actions
O workflow `.github/workflows/ci.yml` passa a executar o Millennium Research Bench em todas as matrizes de teste (Ubuntu, Windows, macOS com Python 3.10 e 3.12) via:
```yaml
- name: Run Millennium Research Bench
  run: python benchmarks/millennium/run_millennium_bench.py
- name: Upload Millennium Scorecard artifact
  uses: actions/upload-artifact@v4
  with:
    name: millennium-scorecard-${{ matrix.os }}-py${{ matrix.python-version }}
    path: benchmarks/millennium/scorecard.json
```

---

## Consequências

- **Rigor Epistemológico**: Distinção clara e honesta entre o que o AXIOM calcula/refuta algebricamente e o status real de problemas abertos milenares.
- **Transparência Auditável**: Métricas calculadas dinamicamente eliminam números arbitrários ou pré-fabricados nos scorecards.
- **Robustez de Domínio e Sintaxe**: Erros de parsing, timeouts ou falhas internas são devidamente reportados como `error` / `unsupported`, sem confusão com refutações adversariais legítimas.
- **Rastreabilidade Contínua**: Cada build em CI gera e arquiva evidências completas e verificáveis do desempenho do motor perante os Sete Problemas do Milênio.
