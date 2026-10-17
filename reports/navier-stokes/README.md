# Equação de Navier-Stokes — Existência e Suavidade

- **Registro:** 17 de outubro de 2026.
- **Status matemático:** **em aberto**, conforme a [página oficial do Clay Mathematics Institute](https://www.claymath.org/millennium/navier-stokes-equation/).
- **Status da investigação:** **propriedades analíticas e controles validados** ([REPORT.md](REPORT.md)). Suíte com 16 critérios automatizados aprovados (100% fail-closed, 0.0% falsos positivos, derivação dinâmica de $E(t) = \pi^2 e^{-4\nu t}$ e $D(t) = 4\nu \pi^2 e^{-4\nu t}$).
- **Referência técnica oficial:** [Existence & Smoothness of the Navier-Stokes Equation (Charles L. Fefferman)](https://www.claymath.org/wp-content/uploads/2022/06/navierstokes.pdf).
- **Objetivo da pasta:** reunir referências, formulação físico-matemática, lemas auxiliares e experimentos com soluções analíticas e identidades de energia.

## Material salvo

- [Relatório de Validação e Integridade](REPORT.md)
- [Evidências integrais da execução](validation.json)
- [Script de reprodução autônomo](validate.py)

---

## Descrição fornecida

Texto em inglês fornecido pelo usuário, preservado como referência:

> This is the equation which governs the flow of fluids such as water and air. However, for many decades no proof was found answering the most basic questions one can ask: do solutions exist, and are they unique? Why ask for a proof? Because a proof gives not only certitude, but also understanding.

---

## Formulação Matemática (Navier-Stokes Incompressível)

As equações de Navier-Stokes para fluido incompressível e viscoso em $\mathbb{R}^3 \times [0, \infty)$ são dadas por:

$$\frac{\partial \mathbf{u}}{\partial t} + (\mathbf{u} \cdot \nabla)\mathbf{u} = -\frac{1}{\rho}\nabla p + \nu \Delta \mathbf{u} + \mathbf{f}(x, t)$$

$$\nabla \cdot \mathbf{u} = 0$$

com condição inicial:

$$\mathbf{u}(x, 0) = \mathbf{u}_0(x)$$

onde:
- $\mathbf{u}(x, t) = (u_1, u_2, u_3) \in \mathbb{R}^3$ é o campo de velocidades do fluido;
- $p(x, t) \in \mathbb{R}$ é o campo de pressão escalar;
- $\nu > 0$ é a viscosidade cinemática do fluido;
- $\rho$ é a densidade (normalizada para $\rho = 1$ no enunciado clássico);
- $\mathbf{f}(x, t)$ é uma força externa aplicada;
- $\mathbf{u}_0(x)$ é o campo de velocidades inicial suave e com divergente nulo ($\nabla \cdot \mathbf{u}_0 = 0$).

### Os quatro enunciados do Prêmio Clay

O Clay Mathematics Institute divide a resolução do problema em quatro cenários possíveis (dos quais a prova de qualquer um concede o prêmio):

1. **(A) Existência global e suavidade em $\mathbb{R}^3$:** para $\mathbf{f} = 0$ e todo dado inicial suave $\mathbf{u}_0$ de decaimento rápido, existe solução clássica suave global no tempo com energia finita:
   $$\sup_{t \ge 0} \int_{\mathbb{R}^3} |\mathbf{u}(x, t)|^2 \, dx < \infty$$
2. **(B) Existência global e suavidade no toro periódico $\mathbb{T}^3 = \mathbb{R}^3 / \mathbb{Z}^3$.**
3. **(C) Ruptura (Blowup / Singularidade) em tempo finito em $\mathbb{R}^3$:** exibição de dado inicial suave $\mathbf{u}_0$ ou força suave $\mathbf{f}$ tal que nenhuma solução suave global exista (formação de singularidade em tempo finito).
4. **(D) Ruptura em tempo finito no toro $\mathbb{T}^3$.**

---

## Roteiro de Investigação com AXIOM

1. **Soluções Exatas Clássicas e Vórtices**:
   - Mapeamento e verificação formal do Vórtice de Taylor-Green e Escoamento de Poiseuille via AXIOM (`exact-symbolic`).
   - Auditoria de divergente nulo $\nabla \cdot \mathbf{u} = 0$ e balanço de momento de Navier-Stokes.

2. **Identidades Fundamentais e Balanço de Energia Dinâmico**:
   - Integração simbólica direta da energia cinética em $L^2$: $E(t) = \pi^2 e^{-4\nu t}$.
   - Derivação analítica da taxa de decaimento $\frac{dE}{dt} = -4\nu \pi^2 e^{-4\nu t}$ e dissipação $D(t) = 4\nu \pi^2 e^{-4\nu t}$.
   - Verificação simbólica da identidade fundamental $\frac{dE}{dt} + D(t) = 0$.

3. **Controles Negativos & Sondas de Fronteira**:
   - Refutação adversarial de conservação de energia sob $\nu > 0$, divergentes não-nulos e viscosidades incompatíveis.
   - Sonda de fronteira perante resolução geral não-linear fechada (recusa fail-closed, preservando honestidade epistemológica).

---

## Evidências AXIOM

O conjunto de evidências e resultados executados está registrado em [REPORT.md](REPORT.md) e [validation.json](validation.json).

> [!IMPORTANT]
> A verificação de soluções particulares, fluxos 2D ou identidades locais no AXIOM não constitui prova do problema geral do Milênio para $3D$. Toda asserção carrega explicitamente seu domínio de validade e grau de garantia (`Guarantee`).

Aplicam-se as [orientações comuns de registro](../README.md#como-registrar-o-trabalho).
