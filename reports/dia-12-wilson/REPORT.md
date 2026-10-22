# Dia 12 — Teorema de Wilson

## Resultado formal

Para todo natural `p ≥ 2`, `IsPrime p ↔ p ∣ fact (p - 1) + 1`,
equivalentemente `(p-1)! ≡ -1 (mod p)`.

- Fonte: [`dia_12_wilson.lean`](../../research/arithmetic/dia_12_wilson.lean).
- Lean **4.14.0 e 4.35.0**: 31 teoremas compilados e auditados por AXIOM.
- Em ambos: `guarantee = formal-proof`, `verification.passed = true`.
- Zero `sorry`; zero axiomas ad-hoc. Dependências fundacionais:
  `propext`, `Classical.choice`, `Quot.sound` (sem confiar no compilador nativo).
- Apenas `Init`; sem Mathlib, sem `Int.emod` e sem pressupor Fermat ou Wilson.

## Referência e correspondência de enunciados

O PDF local de **Brochero et al., Teoria dos Números: Um Passeio pelos Primos
e Outros Números Familiares**, traz o Lema 1.33 na p. 43 e o **Teorema 1.34
(Wilson)** na p. 44, §1.6 (páginas 56–57 do PDF). A indicação anterior
“Cap. 3” do roteiro não corresponde a esta edição.

A definição `IsPrime p` exige `p ≥ 2` e que todo divisor natural seja `1` ou
`p`; `fact 0 = 1` e `fact (n+1) = (n+1) * fact n`; `Cong p a b` significa
`(p : Int) ∣ a - b`. Assim, `wilson_iff` e `wilson_congruence` expressam a
equivalência solicitada. Esta correspondência é uma **inspeção explícita das
definições**, não um certificado automático de equivalência com prosa.

**Limitação preservada:** quando fornecida a descrição em linguagem natural
como `canonical_statement`, o AXIOM retorna `candidate`, `congruent = false`,
`guarantee = unverified`, `verification.passed = false`. Esses resultados
estão separados do certificado da proposição Lean em `validation.json`;
não foram promovidos a alinhamento semântico verificado. O detector textual
de hipóteses também sinaliza os binders do arquivo nessa modalidade.

O “mais precisamente” do livro, sobre `(n-1)! ≡ 0 (mod n)` para compostos
`n ≠ 4`, **não integra o escopo deste dia** e não é declarado provado aqui.

## Estrutura da prova

1. Bézout por indução no algoritmo de Euclides; cancelamento coprimo.
2. Inverso em `1,…,p-1`, normalizado com `Nat.mod`; unicidade.
3. Os únicos resíduos autoinversos são `1` e `p-1` (Lema 1.33).
4. Listas sem repetição fechadas por inversos são decompostas em pares;
   o produto dos resíduos `2,…,p-2` é congruente a `1`.
5. Multiplicar por `p-1` demonstra Wilson, tratando `p=2` separadamente.
6. Na recíproca, um divisor próprio `d` divide `(p-1)!` e `(p-1)!+1`,
   logo divide `1` e é `1`.

Instâncias verificadas no kernel: primos `2, 7, 11`, compostos `4, 9` e o
contraexemplo de fronteira `p=1`. O validador também exige a rejeição real
da afirmação falsa `¬ (1 ∣ 2)` em cada toolchain.

Não foi necessária nova primitiva computacional no AXIOM: a infraestrutura
existente de provas Lean e sessões cobre a tarefa.

## Reprodutibilidade

A partir da raiz, com AXIOM instalado:

```sh
python reports/dia-12-wilson/validate.py --lean-bin /caminho/lean-4.14.0/bin/lean --lean-bin /caminho/lean-4.35.0/bin/lean
```

No PowerShell desta instalação:

```powershell
python reports/dia-12-wilson/validate.py --lean-bin "$env:USERPROFILE\.elan\toolchains\leanprover--lean4---v4.14.0\bin\lean.exe" --lean-bin "$env:USERPROFILE\.elan\toolchains\leanprover--lean4---v4.35.0\bin\lean.exe"
```

Sem argumentos, usa `AXIOM_LEAN_BIN` ou o Lean detectado. O script encerra
com erro em qualquer falha, regenera [`validation.json`](validation.json)
com versões, hashes SHA-256 e auditoria de axiomas por teorema, e salva a
sessão `.axiom/sessions/dia-12-wilson.json`. A sessão contém os certificados
de kernel independentes; sua integridade estrutural não certifica implicações
lógicas entre passos. Os arquivos `.axiom/` são locais e ignorados pelo Git.

O job CI `formal-lean` já compila e audita automaticamente todos os arquivos
`research/arithmetic/*.lean`, incluindo o Dia 12.

## Testes de integração

- `python -m pytest -q -k lean`: 9 testes aprovados no toolchain 4.14.0.
- `python -m pytest -q tests/test_wilson.py`: 3 testes aprovados, incluindo
  exemplos computacionais exatos com as primitivas existentes.
- Suíte completa: 151 aprovados, 6 falhas em `tests/test_literature.py`
  (contratos de citações/classificação, fora das alterações deste dia).
  Nenhum arquivo de implementação ou teste de literatura foi alterado.

O auditor e testes complementares em `research/arithmetic/audit_wilson.py`,
`research/arithmetic/evidence/dia_12_wilson.json` e `tests/test_wilson.py`
foram preservados. O manifesto deste relatório é independente e inclui
explicitamente o controle negativo e a limitação de alinhamento com prosa.

### Revalidação da sessão após persistência

O auditor adicional cria uma sessão temporária para cada toolchain, grava o
resultado e recarrega a sessão via `session("status")`. Só emite evidência se
o passo continuar válido e a garantia permanecer `formal-proof`:

```powershell
python -X utf8 research/arithmetic/audit_wilson.py --lean-bin "$env:USERPROFILE\.elan\toolchains\leanprover--lean4---v4.14.0\bin\lean.exe" --lean-bin "$env:USERPROFILE\.elan\toolchains\leanprover--lean4---v4.35.0\bin\lean.exe" --output research/arithmetic/evidence/dia_12_wilson.json
python -X utf8 -m pytest tests/test_wilson.py -q
```

[`dia_12_wilson.json`](../../research/arithmetic/evidence/dia_12_wilson.json)
liga as duas auditorias ao SHA-256 dos bytes da prova. O checkout do arquivo
Lean usa LF explicitamente, preservando esse hash entre Windows e Linux.
Os testes verificam a ligação ao fonte, exemplos com as primitivas exatas
existentes (`factorial` e resto) e, quando Lean está disponível, repetem a
auditoria real do bicondicional e do caso de fronteira.

### Estado dos testes em 22/10/2026

- `tests/test_wilson.py`: 3 testes aprovados.
- `pytest tests/ -k lean`: 9 testes aprovados com Lean 4.14.0.
- A suíte completa apresenta 6 falhas em `tests/test_literature.py`, cujos
  fontes e testes não foram alterados neste trabalho. Não se declara CI
  integralmente verde a partir das auditorias do Dia 12.
- Pendências de literatura registradas em
  [issue #6](https://github.com/anamnesic/axiom/issues/6), incluindo expectativas
  epistêmicas inadequadas (consulta bibliográfica não é prova matemática),
  contrato de campos MSC e busca no catálogo offline.
