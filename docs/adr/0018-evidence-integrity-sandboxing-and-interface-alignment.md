# ADR-0018: Integridade de Evidências Importadas, Isolamento de Execução e Alinhamento de Interfaces

- **Status**: Aceito (Accepted)
- **Data**: 2026-10-18
- **Versão do AXIOM**: v0.2.7
- **Autores**: Equipe de Arquitetura AXIOM & Chronokairo Research

---

## Contexto & Problema

Na revisão da versão v0.2.6 (commit `a5261b2`), foram identificados pontos críticos de confiança indevida e desalinhamento de interfaces:
1. **Confiança em JSON Importado**: `ResearchSession.load()` apenas desconfiava de `formal-proof`, permitindo que etapas com garantias matemáticas declaradas (`exact-symbolic`, `verified-substitution`) mantivessem `step_valid=True` sem revalidação local. O campo `revalidated_locally` podia ser lido diretamente do JSON falso.
2. **Isolamento de Processos Lean**: O uso de diretórios temporários e flags `-M`/`-T` não garantia isolamento contra metaprogramação ou vazamento de variáveis de ambiente do usuário.
3. **Ambiguidade entre Integridade do Grafo e Implicação Matemática**: O campo `chain_valid` verificava a topologia de dependências do DAG, mas podia sugerir falsamente dedução matemática entre etapas independentes.
4. **Desalinhamento de Comandos**: Algumas opções documentadas em `docs/use-cases.md` (como `--tolerance` no `compare` e subcomandos de `session`) não estavam expostas nas interfaces CLI e MCP.
5. **Cálculo de Métricas em Benchmarks**: O runner de benchmark precisava derivar todas as contagens estritamente de casos atômicos, rejeitando relatórios adulterados.

---

## Decisões de Arquitetura

### 1. Modelo de Desconfiança Total para Sessões Importadas
- Toda entrada carregada de um arquivo JSON inicia obrigatoriamente com:
  - `imported = True`
  - `revalidated_locally = False` (ignorando qualquer valor contido no JSON)
  - `step_valid = False`
  - Garantias rebaixadas a `Guarantee.UNVERIFIED`
- A promoção para garantias superiores exige a execução explícita de `revalidate_step()` ou `revalidate_all()` no ambiente local.

### 2. Isolamento de Processos e Sanitização de Ambiente
- Em `LeanEngine.prove()`, o ambiente de execução (`env`) do subprocesso é estritamente sanitizado:
  - `PATH` filtrado apenas para os binários estritamente necessários;
  - `HOME` apontado para um diretório temporário isolado;
  - Remoção de variáveis sensíveis de ambiente, tokens e credenciais;
  - Aplicação de limites de execução (`-M 2048`, `-T 100000`) e timeout estrito.

### 3. Separação Explícita de Validade de Dependências
- Distinção clara na documentação e metadados:
  - `dependency_integrity_valid`: integridade topológica do DAG (sem dependências ausentes, ciclos ou referências futuras);
  - `logical_implication_proven`: certificação matemática de que a conclusão do passo antecedente é formalmente utilizada como hipótese do passo seguinte.

### 4. Alinhamento de Interfaces CLI e MCP
- `axiom compare` e `math_compare` passam a aceitar `--tolerance` (e alias `a`/`b` para `left`/`right`);
- `axiom session` suporta subcomandos `new --title ...`, `status`, e `record --step ... --command ... --depends-on ...`;
- Suíte automatizada de testes sem mocks (`tests/test_use_cases.py`) assegura conformidade contínua com `docs/use-cases.md`.

### 5. Recálculo Atômico e Proteção contra Adulteração de Benchmarks
- Métricas de benchmarks são recalculadas a partir dos registros atômicos individuais, tratando divisões por zero com `null`/`None` em vez de 100%;
- Testes adversariais comprovam a rejeição de relatórios adulterados que apresentem métricas inconsistentes com seus casos de teste.
