# Relatório de Validação e Integridade: Equação de Navier-Stokes no AXIOM

Data de execução e consulta às fontes: 17 de outubro de 2026.  
Escopo: Validação analítica e numérica rigorosa de soluções exatas (Vórtice de Taylor-Green, Escoamento de Poiseuille), balanço de quantidade de movimento, incompressibilidade ($\nabla \cdot \mathbf{u} = 0$), taxa de dissipação de energia cinética em $L^2$ e controles negativos estritos sob o motor AXIOM v0.2.2.  
**Nenhuma demonstração de existência global suave ou ruptura (blowup) foi fornecida ou produzida.** O Clay Mathematics Institute continua classificando o problema como aberto ([Página oficial do Clay](https://www.claymath.org/millennium/navier-stokes-equation/)).

---

## 1. Fundamentos e Resultados Obtidos

As equações de Navier-Stokes para fluidos incompressíveis governam o campo de velocidades $\mathbf{u}(x, t)$ e a pressão escalar $p(x, t)$:

$$\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u} \cdot \nabla)\mathbf{u} = -\nabla p + \nu \Delta \mathbf{u} + \mathbf{f}$$
$$\nabla \cdot \mathbf{u} = 0$$

### 1.1. Incompressibilidade e Vórtice de Taylor-Green
No escoamento bidimensional periódico de Taylor-Green com viscosidade $\nu > 0$:
$$u(x, y, t) = \sin(x)\cos(y)e^{-2\nu t}, \quad v(x, y, t) = -\cos(x)\sin(y)e^{-2\nu t}$$
- **Divergente nulo**: $\nabla \cdot \mathbf{u} = \partial_x u + \partial_y v = \cos(x)\cos(y)e^{-2\nu t} - \cos(x)\cos(y)e^{-2\nu t} \equiv 0$. O AXIOM comprovou a identidade com garantia `exact-symbolic` e resíduo 0.
- **Controle negativo**: Campo não-solenoidal $\mathbf{u} = (x^2, y^2)$ possui divergente $\nabla \cdot \mathbf{u} = 2x + 2y \neq 0$. O AXIOM refutou a afirmação com `status = disproven`, encontrando contraexemplo $(x=-1, y=2)$ e atribuindo `guarantee = unverified` (`verification.passed = false`).

### 1.2. Balanço de Quantidade de Movimento (Navier-Stokes)
Para o campo de pressão $p(x, y, t) = \frac{1}{4}(\cos(2x) + \cos(2y))e^{-4\nu t}$:
- Termo convectivo: $(\mathbf{u} \cdot \nabla)\mathbf{u} = \frac{1}{2}\sin(2x)e^{-4\nu t} \hat{\mathbf{i}} + \frac{1}{2}\sin(2y)e^{-4\nu t} \hat{\mathbf{j}}$.
- Gradiente de pressão: $\nabla p = -\frac{1}{2}\sin(2x)e^{-4\nu t} \hat{\mathbf{i}} - \frac{1}{2}\sin(2y)e^{-4\nu t} \hat{\mathbf{j}}$.
- Termo viscoso: $\nu \Delta \mathbf{u} = -2\nu \mathbf{u} = \frac{\partial \mathbf{u}}{\partial t}$.
- O balanço de momento total cancela-se identicamente a 0, verificado pelo AXIOM como `exact-symbolic`.
- **Controle negativo**: Simulação com parâmetro de viscosidade incompatível ($\nu' = 2\nu$) deixa resíduo não-nulo e foi rejeitada com `status = disproven`.

### 1.3. Dissipação de Energia Cinética em $L^2$
A energia cinética total no toro periódico $[0, 2\pi]^2$ decai exponencialmente:
$$E(t) = \int_{[0, 2\pi]^2} \frac{1}{2}|\mathbf{u}|^2 dx dy = \frac{\pi^2}{2} e^{-4\nu t}$$
$$\frac{dE}{dt} = -2\nu \pi^2 e^{-4\nu t} = -\nu \int |\nabla \mathbf{u}|^2 dx dy$$
- O balanço $\frac{dE}{dt} + \nu \|\nabla \mathbf{u}\|_{L^2}^2 = 0$ foi validado com garantia `exact-symbolic`.
- **Controle negativo de conservação**: A asserção de que a energia é constante ($\frac{dE}{dt} = 0$) em regime viscoso ($\nu > 0, t > 0$) foi refutada fail-closed pelo AXIOM com contraexemplo sob hipóteses relacionais.

### 1.4. Escoamento Laminar de Poiseuille e Integridade de Domínio
No escoamento estacionário entre placas paralelas em $y \in [-h, h]$, a velocidade é $u(y) = \frac{P}{2\mu}(h^2 - y^2)$, onde $P = -\frac{dp}{dx} > 0$ e $\mu > 0$ é a viscosidade dinâmica.
- Com a hipótese explícita de viscosidade não-nula (`-A "mu>0"`), o AXIOM comprovou o balanço de forças $\mu \frac{d^2 u}{dy^2} + P = 0$ com garantia `exact-symbolic`.
- Sem a hipótese de domínio, o motor identificou a restrição de domínio em $\mu = 0$ e barrou a equivalência universal, demonstrando a robustez contra divisões por zero e singularidades físicas.

---

## 2. Resumo da Execução de Controle

Todos os 13 testes do script de validação foram aprovados com 100% de comportamento fail-closed:

| Verificação | Garantia AXIOM | `verification.passed` | Interpretação Científica |
|---|---|---|---|
| Autotestes do ambiente (`doctor`) | N/A | `true` | Ambiente íntegro e autotestes do núcleo aprovados |
| Divergente do Vórtice de Taylor-Green | `exact-symbolic` | `true` | Incompressibilidade comprovada simbolicamente |
| Controle de campo não-solenoidal | `unverified` | `false` | Divergente não-nulo refutado via contraexemplo |
| Balanço de momento em $x$ (Taylor-Green) | `exact-symbolic` | `true` | Solução clássica exata satisfaz Navier-Stokes |
| Controle de incompatibilidade de viscosidade | `unverified` | `false` | Resíduo não-nulo refutado fail-closed |
| Balanço da taxa de dissipação de energia | `exact-symbolic` | `true` | Identidade de dissipação em $L^2$ verificada |
| Controle de energia constante sob $\nu > 0$ | `unverified` | `false` | Afirmação fisicamente impossível refutada |
| Identidade de Poisson para a pressão | `exact-symbolic` | `true` | Equação de compatibilidade da pressão comprovada |
| Balanço de momento no escoamento de Poiseuille | `exact-symbolic` | `true` | Escoamento estacionário verificado sob $\mu > 0$ |
| Controle de condição de contorno em Poiseuille | `unverified` | `false` | Violação de contorno aderente $u(\pm h) = 0$ refutada |
| Tentativa de solução geral não-linear fechada | `unverified` | `false` / `None` | Recusa fail-closed perante problema não-linear aberto |
| MCP stdio: Divergente de Taylor-Green | `exact-symbolic` | `true` | Verificação via protocolo JSON-RPC 2.0 aprovada |
| MCP stdio: Controle não-solenoidal | `unverified` | `false` | Rejeição via protocolo JSON-RPC 2.0 confirmada |

---

## 3. Reprodutibilidade e Evidências

Para reproduzir integralmente os experimentos a partir da raiz do repositório:

```powershell
python reports/navier-stokes/validate.py
```

O script regera [`reports/navier-stokes/validation.json`](validation.json), contendo:
- Metadados de ambiente e hashes SHA-256 de todos os arquivos relevantes.
- Saídas JSON completas de todas as execuções CLI do AXIOM.
- Requisições e respostas JSON-RPC 2.0 completas do servidor MCP por stdio.
