# ADR-0010: Integridade de Domínio, Hipóteses Explícitas e Governança de Singularidades

- **Status**: Aceito (Accepted)
- **Data**: 2026-10-17
- **Versão do AXIOM**: v0.2.1

## Contexto

A revisão da versão v0.2.0 e os experimentos de campo em problemas abertos (Millennium Problems — Hipótese de Riemann) evidenciaram 4 vulnerabilidades semânticas presentes em sistemas de álgebra computacional convencionais:

1. **Semântica Complexa vs. Real**: Símbolos não restritos pertencem a $\mathbb{C}$ por padrão. Contudo, CAS ingênuos assumiam tacitamente símbolos reais, declarando $\sqrt{x^2} = |x|$ sem hipóteses, ignorando o contraexemplo $x = i$ onde $\sqrt{i^2} = i \neq 1 = |i|$.
2. **Perda Silenciosa de Denominadores**: Ao avaliar $\frac{x-1}{x-1}$, o SymPy cancelava o numerador e denominador imediatamente para `1` durante a construção da árvore AST, eliminando a restrição de domínio $x \neq 1$.
3. **Ausência de Hipóteses no MCP e CLI**: O esquema MCP e os subcomandos de linha de comando não expunham o parâmetro de hipóteses (`assumptions`), forçando o agente a operar apenas com o domínio padrão não-configurado.
4. **Ambiguidade entre Raízes Amostrais e Completude de Conjuntos Solução**: Equações periódicas como $\sin(x) = 0$ retornavam `["0", "pi"]` sem indicar se a lista era finita e exaustiva.

## Decisões de Arquitetura

1. **Rastreamento de Denominadores na AST**:
   O `Parser` agora inspeciona e armazena os denominadores sintáticos (`denominators` e `domain_constraints`) antes que o operador de divisão do SymPy avalie o quociente. Operações de `compare` detectam incompatibilidade de domínio (`domain-mismatch`), recusando elevação para `exact-symbolic` sem hipóteses que descartem os pontos singulares.
2. **Sondagem Complexa Gaussiana Inicial**:
   A sequência de sondagem em `_build_probe_sequence` inclui valores gaussianos complexos ($i, -i, 1+i$) para símbolos sem restrição explícita de que são reais, refutando branch cuts inválidos em $\mathbb{C}$ imediatamente.
3. **Exposição de Hipóteses no MCP e CLI**:
   - Adicionada a propriedade `"assumptions"` com suporte a dicionário e strings compostas (`"x:positive"`, `"x:real,nonzero;y:positive"`) no `inputSchema` de `math_parse`, `math_simplify`, `math_solve`, `math_differentiate`, `math_integrate`, `math_limit`, `math_evaluate`, `math_verify` e `math_compare`.
   - Adicionado o argumento `-A` / `--assumptions` a todos os comandos equivalentes da CLI.
4. **Metadados de Completude de Solução**:
   O campo `solution_complete: bool` foi introduzido em `MathResult.verification.data`, diferenciando polinômios (completude garantida) de equações transcendentais e periódicas (`solution_complete = false`, com representação `solution_set = ImageSet`).
5. **Auditoria Fail-Closed de Limites e Singularidades de Integrais**:
   - `verify_limit` rejeita $oo \neq -oo$ e infinitos não-assinados (`zoo`).
   - `verify_integral` e `nintegrate` identificam polos internos e suportam limites infinitos (`mp.inf`).
   - Suporte ao ponto de entrada de módulo `python -m axiom` via `src/axiom/__main__.py`.

## Consequências

- **Acurácia**: No benchmark EXP-0001, o AXIOM atingiu **0.0% de taxa de falsos positivos** e **100% de comportamento fail-closed** contra 33.3% de falsos positivos do baseline de CAS ingênuo.
- **Transparência**: Toda hipótese ativa é registrada nos campos `Evidence.steps`, `MathResult.warnings` e `Verification.data["assumptions"]`.
- **Compatibilidade**: Total retrocompatibilidade com a API v0.2.0 e conformidade rigorosa com o protocolo MCP.
