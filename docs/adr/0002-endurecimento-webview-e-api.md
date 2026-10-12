# ADR 0002 — Endurecimento da webview e da API local

- **Status:** Aceito
- **Data:** 2026-10-12
- **Contexto:** Revisão de segurança semanal (issue #4)

## Contexto

A revisão semanal encontrou um **XSS (ALTO, 9/10)** no console SymPy,
verificado ponta a ponta: `SympyConsole.jsx` injetava o campo `latex`
(retornado pelo backend como `sp.latex(...)` de uma expressão do usuário)
direto no DOM via `dangerouslySetInnerHTML`, sem escape. Como a DSL
deliberadamente aceita strings arbitrárias como nomes em
`Symbol()`/`Function()`/`symbols()` (ADR 0001, item 4), um snippet
compartilhado como `x = Symbol('<img src=x onerror=...>')` executava
script na webview privilegiada do Tauri — com acesso a
`window.__TAURI_INTERNALS__` e à capability `shell:allow-open` (não usada
pelo app). Agravantes: `"csp": null` no `tauri.conf.json` (nenhuma
Content-Security-Policy) e `new Function` com input do usuário no
`Viz2D.jsx` (eval-equivalente). Ainda: o sidecar FastAPI em
127.0.0.1:8080 não validava o header `Host`, expondo a API a DNS
rebinding; o Monaco era carregado de CDN (jsdelivr) em vez de local;
e o `Cargo.toml` referenciava a feature `shell-open`, que não existe no
Tauri 2 (o lado Rust nunca chegou a compilar — não há `Cargo.lock`).

## Decisão

1. **XSS do console:** renderizar `cell.output.latex` com
   `katex.renderToString(..., { throwOnError: true, trust: false })`
   com fallback para texto escapado — mesmo padrão já usado no
   `Editor.jsx`. Defesa em profundidade no backend: `_validate_symbol_names`
   em `safe_math.py` restringe nomes passados a `symbols`/`Symbol`/
   `Function`/`Wild`/`Dummy` a `[\w:]+` por nome (unicode + `:` para
   ranges como `symbols('x:5')`), eliminando metacaracteres de HTML.
2. **Viz2D:** manter `new Function`, mas precedido de whitelist estrita
   (`isSafePlotExpression`): só caracteres matemáticos e identificadores
   de uma lista fechada (`Math`, `sin`, `x`, `PI`, ...) — bloqueia
   `window`, `__TAURI_INTERNALS__`, `fetch`, `constructor` etc.
3. **CSP:** definir política estrita no `tauri.conf.json`
   (`script-src 'self'`, `connect-src` limitado ao sidecar e ao IPC do
   Tauri, fontes apenas do Google Fonts usado pelo `index.html`).
   `style-src 'unsafe-inline'` é necessário para o KaTeX (atributos de
   estilo na saída renderizada).
4. **Capabilities:** remover `shell:allow-open` (nunca usada) e fixar
   `args: false` no sidecar `shell:allow-execute` (o binário não aceita
   argumentos). Remover a feature inexistente `shell-open` do `tauri`
   no `Cargo.toml` (corrige o build Rust latente).
5. **API local:** middleware `enforce_local_origin` no `backend/main.py`
   rejeita `Host` fora de `{localhost, 127.0.0.1, ::1}` (bloqueia DNS
   rebinding) e requisições de escrita com `Origin` fora da allowlist do
   CORS. Pré-requisito antes de qualquer futuro trabalho no bridge Lean
   (`/verify` compila código Lean do usuário por design).
6. **Monaco local:** configurar `loader.config({ monaco })` com o pacote
   `monaco-editor` empacotado pelo Vite (workers via `?worker`) — elimina
   a carga de script de CDN na webview e viabiliza `script-src 'self'`.
7. **Supply chain:** `download-model.ps1` reescrito para o formato atual
   do Hugging Face (2 partes) com verificação SHA-256 de cada parte antes
   de concatenar; `package-lock.json` passa a ser commitado (removido do
   `.gitignore`) para builds reproduzíveis e Dependabot efetivo.
8. **Dependências:** floors elevados para versões sem CVEs conhecidos
   (OSV): `python-multipart>=0.0.31`, `katex ^0.18.2`, `vite ^6.4.3`,
   `vitest ^4.1.11`, `tauri 2.11.1`, `tauri-plugin-shell 2.2.1`.

## Consequências

- **Positivas:** XSS eliminado no sink e na origem; execução de script
  restrita a código empacotado (`'self'`); superfície IPC reduzida ao
  sidecar; API imune a rebinding; downloads do modelo verificados por
  hash; 146 testes backend + build frontend passando (11 novos testes de
  regressão em `test_security.py`).
- **Negativas:** expressões de plotagem ficam limitadas à whitelist de
  identificadores (funções fora da lista precisam ser adicionadas
  manualmente); o CSP precisa ser revisado se novas origens de fonte ou
  API forem introduzidas.
- **Riscos futuros:** `Cargo.lock` ainda não existe — commitá-lo no
  primeiro build Rust (`cargo tauri build`) para fixar a árvore de
  dependências; o endpoint `/verify` continuará sendo RCE-by-design
  quando o bridge Lean passar a compilar código de fato — nessa altura,
  considerar token de autenticação no sidecar.
