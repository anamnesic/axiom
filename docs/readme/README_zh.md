# AXIOM

**数学推理引擎**

*一个用于数学计算、探索与验证的 MCP。*

[English](../../README.md) · **简体中文** · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md)

AXIOM 是面向 AI 智能体、研究人员、学生和开发者的计算数学基础设施。它通过统一的契约，将任何 MCP 客户端连接到专业数学引擎 —— SymPy、SciPy、SageMath、Lean 4 —— 并提供可追溯、**可独立验证**的结果。

它不是一个由 AI 驱动的计算器。它不是另一个 Mathematica、SageMath 或 Lean。它是让智能体通过单一接口使用上述所有引擎的基础设施。

> 受 [REA](https://github.com/morluto/rea) 理念启发：*逆向工程一切* → **分析数学**。

## 为什么选择 AXIOM

智能体可能会声称它解出了一个方程。AXIOM 会在结果被信任之前**要求独立验证**。

```
math solve "x^2 - 5*x + 6 = 0"
```

```text
┌─────────────────────────────────────────────────┐
│ 二次方程                                        │
│   x² - 5x + 6 = 0                               │
│                                                 │
│ 解                                              │
│   x = 2  或  x = 3                              │
│                                                 │
│ 引擎          SymPy                             │
│ 验证          精确代入（分数）                  │
│ 保证          VERIFIED-SUBSTITUTION             │
│ 结果          两个根均满足该方程                │
└─────────────────────────────────────────────────┘
```

### 保证等级

并非每个数学结果都具有相同的逻辑强度。AXIOM 明确区分每一个等级：

| 等级 | 含义 |
| --- | --- |
| `exact-symbolic` | 已验证的符号恒等式（例如规范化简） |
| `verified-substitution` | 通过精确算术代入验证的解 |
| `numerical-approximation` | 带声明误差的数值近似 |
| `formal-proof` | 由证明内核（Lean 4）验证的证明 |
| `heuristic` | 可能的结果，尚未完全验证 |
| `unverified` | 原始计算，尚未验证 |

每个结果都带有证据元数据：`engine`、`engine_version`、`steps`、`limitations` 和 `reproducible_with`。

## 理念（继承自 REA）

| REA | AXIOM |
| --- | --- |
| 逆向工程一切 | 分析数学 |
| 二进制分析 | 表达式与结构分析 |
| Ghidra / Hopper / IDA | SymPy / SageMath / Julia / Lean 4 |
| 代码追踪 | 解追踪 |
| 逆向工程证据 | 数学证据 |
| 反编译 | 化简与代数分解 |
| 函数检查 | 函数分析 |
| 行为比较 | 等价性验证 |
| 面向智能体的 MCP | 面向数学智能体的 MCP |
| CLI | 数学 CLI |

## 架构

```text
┌──────────────────────────────────────────────────────────┐
│  AI 智能体                                               │
│  Codex · Claude Code · Gemini CLI · 其他 MCP 客户端      │
└────────────────────────┬─────────────────────────────────┘
                         │  MCP / CLI
┌────────────────────────▼─────────────────────────────────┐
│  AXIOM 核心                                              │
│  解析器 · 调度器 · 引擎注册表 · 证据 ·                   │
│  验证                                                    │
└──┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
 符号        数值        形式化      可视化
 SymPy      SciPy       Lean 4     Plotly · Manim
 SageMath   Julia       Mathlib
```

无论由哪种软件执行计算，同一契约始终成立：更换引擎既不会改变结果格式，也不会改变保证等级。

## 模块

| 模块 | 能力 |
| --- | --- |
| `arithmetic` | 精确算术、分数、任意精度 |
| `algebra` | 方程、多项式、因式分解、化简 |
| `calculus` | 极限、导数、积分、级数 |
| `linear-algebra` | 矩阵、特征值、分解 |
| `geometry` | 欧几里得几何、解析几何与微分几何 |
| `number-theory` | 素数、同余、丢番图方程 |
| `discrete` | 组合学、图论、逻辑 |
| `statistics` | 概率、分布、推断 |
| `optimization` | 线性、非线性与凸优化 |
| `differential-equations` | 常微分方程、偏微分方程与动力系统 |
| `numerical` | 数值方法、近似与误差 |
| `symbolic` | 通用符号操作 |
| `proof` | 证明、反例与形式化验证 |
| `visualization` | 二维/三维绘图、动画与向量场 |
| `research` | 猜想探索、假设与实验 |

## MCP 工具

小型、可组合的工具：

```
math_parse        math_simplify     math_solve
math_differentiate   math_integrate  math_limit
math_evaluate      math_plot         math_prove
math_verify        math_explain      math_compare
math_explore
```

提议的 CLI：

```bash
math solve "x^2 - 5*x + 6 = 0"
math integrate "sin(x)^2" --variable x
math plot "sin(x)/x" --range -10:10
math prove theorem.lean --engine lean
math verify solution.json
```

## 路线图

- [ ] **v0.1 — 基础**：CLI、MCP、表达式解析器、SymPy、方程求解与证据。
- [ ] **v0.2 — 数值**：SciPy、矩阵、数值积分、优化与误差评估。
- [ ] **v0.3 — 验证**：独立验证器与可选的 Lean 4 集成。
- [ ] **v0.4 — 可视化**：交互式绘图、几何与动力系统可视化。
- [ ] **v1.0 — 研究**：自动化工具组合、可复现实验与辅助猜想探索。

我们从三个引擎开始：**SymPy**（符号）、**SciPy**（数值）和 **Lean 4**（形式化证明）。

## 仓库结构

```
axiom/
├── README.md
├── LICENSE
├── AGENTS.md
├── Cargo.toml
├── crates/
│   ├── core/
│   ├── cli/
│   ├── mcp/
│   ├── evidence/
│   ├── verification/
│   └── engine-registry/
├── engines/
│   ├── sympy/
│   ├── sagemath/
│   ├── scipy/
│   ├── julia/
│   └── lean/
├── domains/
│   ├── algebra/
│   ├── calculus/
│   ├── geometry/
│   ├── discrete/
│   ├── number-theory/
│   ├── dynamical-systems/
│   └── optimization/
├── skills/
│   └── mathematics/
├── examples/
├── benchmarks/
├── tests/
└── docs/
```

## 名称

**AXIOM** —— *数学推理引擎*。它拥有独立的身份，与形式数学和研究相一致。

## 许可证

MIT

## 与 MathTools Offline 的关系

本仓库曾是 *MathTools Offline*（一个面向 LaTeX/SymPy/Lean 的离线桌面套件）。它被更名为 **AXIOM**，并重新定位为面向智能体的计算数学基础设施。引擎（SymPy、Lean 4）在概念上是共享的，但如今的重点是统一的 MCP 契约与结果的独立验证。
