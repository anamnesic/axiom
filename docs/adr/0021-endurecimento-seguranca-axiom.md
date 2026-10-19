# ADR 0021 — Endurecimento de higiene de CI e scripts de toolchain

## Status

Aceito

## Data

2026-02-14

## Contexto

Uma revisão de segurança identificou quatro achados de severidade baixa,
relativos à higiene do pipeline de CI e dos scripts de provisionamento de
toolchains:

1. **Instalador elan em ref mutável via `curl | sh`** — `.github/workflows/ci.yml`
   (job `formal-lean`), `scripts/install_toolchains.sh` e
   `scripts/install_toolchains.ps1` baixavam `elan-init.sh`/`elan-init.ps1` de
   `raw.githubusercontent.com/leanprover/elan/master/...` e o executavam
   imediatamente. Um push para `master` do upstream (ou um comprometimento
   desse repositório) alteraria silenciosamente o código executado no CI e nas
   máquinas de desenvolvedores, sem qualquer rastreabilidade no nosso histórico.
2. **Permissões implícitas do GITHUB_TOKEN** — o workflow não declarava bloco
   `permissions`, herdando a política padrão da organização/repositório
   (frequentemente `read/write`), e os checkouts persistiam credenciais no
   workspace, ampliando o raio de um possível comprometimento por injeção em
   steps posteriores.
3. **Installer da Julia sem verificação** — `install_toolchains.sh` executava
   `curl -fsSL https://install.julialang.org | sh` diretamente da CDN, sem
   validar o conteúdo recebido.
4. **Branches remotas órfãs do dependabot** — duas branches
   `dependabot/npm_and_yarn/...` sem PR aberto associado acumulavam-se no
   remoto, poluindo o namespace e mantendo referências a dependências
   desatualizadas.

Os três alertas de code scanning remanescentes referem-se a código já
removido da branch `main` e não exigem alteração de código-fonte.

## Decisão

1. **Pinamento do elan a commit SHA** — todas as referências ao instalador do
   elan agora apontam para o commit `9605b24b08cf68b78dce0014b6fa01be1f8e2cee`
   (HEAD de `master` de `leanprover/elan` na data desta decisão):
   `https://raw.githubusercontent.com/leanprover/elan/9605b24b08cf68b78dce0014b6fa01be1f8e2cee/elan-init.sh`
   (e o correspondente `elan-init.ps1`). Um commit SHA é imutável: qualquer
   mudança upstream passa a exigir uma alteração explícita e revisável neste
   repositório.
2. **Princípio do menor privilégio no CI** — adicionado `permissions:
   contents: read` no topo do workflow e `persist-credentials: false` em todos
   os três steps `actions/checkout@v4` (jobs `test`, `formal-lean` e
   `build-dist`). Nenhum job do workflow publica no repositório; o job de
   publish de release, quando existir, declarará suas próprias permissões.
3. **Installer da Julia com verificação** — o installer da juliaup é servido
   por CDN (`install.julialang.org`) sem ref pinnável por commit; o script
   agora o baixa para arquivo temporário (`mktemp`), valida tamanho e shebang
   e só então o executa, removendo o arquivo em seguida.
4. **Limpeza de branches órfãs** — deletadas do remoto
   `dependabot/npm_and_yarn/npm_and_yarn-24f7d00a0f` e
   `dependabot/npm_and_yarn/npm_and_yarn-ab4fad088c` (confirmadas sem PR
   associado antes da remoção).

## Consequências

- **Positivas:** o CI e os scripts de setup executam exatamente o instalador
  revisado; o token do workflow tem acesso somente-leitura e não deixa
  credenciais no workspace; o namespace de branches remotas contém apenas
  `main`.
- **Negativas:** atualizações do elan exigem bump manual do SHA pinnado
  (desejável, pois força revisão consciente); o installer da juliaup continua
  mutável por natureza — a validação de shebang/tamanho mitiga execução
  acidental de conteúdo corrompido, mas não substitui uma assinatura
  criptográfica, inexistente no upstream.
- **Neutral:** o comportamento funcional do CI e dos instaladores permanece
  idêntico; os alertas de code scanning legados (código deletado) permanecem
  como estão, por não existirem mais no `main`.
