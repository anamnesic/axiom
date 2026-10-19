# ADR-0022: Robustez de Codificação UTF-8 em Subprocessos, API Direta de Sessão e Formalização do Lema de Euclides

**Status:** Aceito  
**Data:** 19 de Outubro de 2026  
**Contexto:** Investigação Matemática Contínua (Dia 05 do Currículo de Aritmética) e Auditoria de Execução

---

## 1. Contexto e Motivação

Durante a formalização do **Dia 04** (Identidade de Bézout) e a preparação para o **Dia 05** (Lema de Euclides para Números Primos), três atritos e vulnerabilidades operacionais foram descobertos no Chronokairo AXIOM:

1. **Falha de Decodificação UTF-8 no Windows (`UnicodeDecodeError` / cp1252):**
   No Windows, chamadas a `subprocess.run(..., text=True)` sem especificação explícita de `encoding="utf-8"` utilizam a codificação padrão do sistema operacional (geralmente `cp1252`). Quando o kernel do Lean 4 imprime símbolos lógicos avançados e caracteres matemáticos Unicode (`⊢`, `∣`, `≠`, `⬝`, etc.) em mensagens de diagnóstico ou erros de tática, a thread de leitura do subprocesso Python lança `UnicodeDecodeError`, deixando `proc.stdout` como `None` e resultando em colapso com `TypeError: unsupported operand type(s) for +: 'NoneType' and 'str'`.

2. **Atrito na API de Sessões de Pesquisa (`ax.session("record", ...)`):**
   Anteriormente, o método `Axiom.session(action="record")` exigia obrigatoriamente reexecutar uma computação a partir de uma string de expressão ou de um comando de linha de comando (`axiom solve...`). Não era possível passar diretamente um objeto `MathResult` já computado ou um arquivo formal (`--file`). Isso forçava reexecuções desnecessárias ou manipulação manual de arquivos internos da sessão.

3. **Resolução Formal do Lema de Euclides com Zero Sorry e Axiomas Canônicos:**
   A prova de que $p \mid ab \implies p \mid a \lor p \mid b$ para $p$ primo exigia formalizar tanto a identidade de Bézout quanto o lema de divisibilidade para números coprimos ($\gcd(a, b) = 1 \land a \mid bc \implies a \mid c$), com auditoria estrita `#print axioms Dia05EuclidLemma.*`.

---

## 2. Decisões Arquiteturais

### D1: Codificação Explícita UTF-8 com Substituição Segura em Todos os Motores
- Em `src/axiom/engines/lean_engine.py`:
  - `_detect_version` e `prove` passam a utilizar explicitamente `encoding="utf-8", errors="replace"`.
  - Tratamento de `proc.stdout` e `proc.stderr` protegido contra `NoneType`:
    ```python
    raw_output = f"{proc.stdout or ''}\n{proc.stderr or ''}"
    diagnostics = [line for line in raw_output.splitlines() if line.strip()]
    ```
- Em `src/axiom/engines/external_engines.py`:
  - Motores externos (SageMath e Julia) passam a usar `encoding="utf-8", errors="replace"` em `subprocess.run`.

### D2: Expansão da API de Gravação de Sessões (`result` e `--file`)
- O método `Axiom.session` agora aceita:
  - `result: MathResult | None = None`: registra diretamente um resultado matemático já validado, preservando sua cadeia de garantias e metadados.
  - `file: Path | str | None = None`: despacha automaticamente arquivos `.lean` para `self.prove(str(file))` ou arquivos de script para resolução, registrando na sessão.
  - Parser robusto de tokens para `command="axiom prove ..."` no CLI e em chamadas programáticas.
- A CLI de sessão passa a expor `--file`:
  ```bash
  axiom session record --name dia-05-euclid-lemma --file build/book_investigation/dia_05_euclid_lemma.lean --note "..."
  ```

### D3: Formalização do Dia 05 (Lema de Euclides para Números Primos)
- Arquivo: `build/book_investigation/dia_05_euclid_lemma.lean`.
- Teoremas certificados pelo kernel Lean 4 (v4.35.0):
  - `Dia05EuclidLemma.hefez_bezout_algebra`: reorganização de retrosubstituição de Euclides.
  - `Dia05EuclidLemma.hefez_bezout_identity`: identidade linear de Bézout em $\mathbb{Z}$.
  - `Dia05EuclidLemma.hefez_coprime_dvd_mul_int`: lema linear de coprimaridade em $\mathbb{Z}$.
  - `Dia05EuclidLemma.hefez_coprime_dvd_mul`: Corolário 3.4 de Abramo Hefez sobre coprimos em $\mathbb{N}$.
  - `Dia05EuclidLemma.hefez_prime_gcd_cases`: dicotomia do MDC de primo ($\gcd(p, a) = 1 \lor \gcd(p, a) = p$).
  - `Dia05EuclidLemma.hefez_euclid_lemma`: Lema de Euclides para números primos.
- Garantia: `formal-proof` (0 `sorry`, 0 axiomas não confiáveis, dependente apenas de `propext` e `Quot.sound`).

---

## 3. Consequências e Benefícios

- **Imunidade a Falhas de Decodificação:** O AXIOM agora processa saídas de diagnósticos ricos e caracteres Unicode do Lean 4 em Windows, macOS e Linux sem risco de `UnicodeDecodeError` ou `TypeError`.
- **Experiência de Pesquisa Fluida:** Agentes e pesquisadores podem provar teoremas e registrá-los em uma única instrução limpa via Python (`ax.session("record", result=res)`) ou CLI (`axiom session record --file ...`).
- **Validação Cumulativa do Livro:** 5 de 120 dias do currículo de matemática concluídos e verificados no kernel.
