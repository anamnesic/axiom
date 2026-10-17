# AXIOM

**數學推理引擎**

*一個用於數學計算、探索與驗證的 MCP。*

[English](../../README.md) · [简体中文](README_zh.md) · **繁體中文** · [日本語](README_ja.md) · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md)

AXIOM 是面向 AI 代理、研究人員、學生與開發者的計算數學基礎設施。它透過統一的契約，將任何 MCP 用戶端連接到專業數學引擎 —— SymPy、SciPy、SageMath、Lean 4 —— 並提供可追溯、**可獨立驗證**的結果。

它不是一個由 AI 驅動的計算器。它不是另一個 Mathematica、SageMath 或 Lean。它是讓代理透過單一介面使用上述所有引擎的基礎設施。

> 受 [REA](https://github.com/morluto/rea) 理念啟發：*逆向工程一切* → **分析數學**。

## 為什麼選擇 AXIOM

代理可能會聲稱它解出了一個方程式。AXIOM 會在結果被信任之前**要求獨立驗證**。

```
math solve "x^2 - 5*x + 6 = 0"
```

```text
┌─────────────────────────────────────────────────┐
│ 二次方程式                                      │
│   x² - 5x + 6 = 0                               │
│                                                 │
│ 解                                              │
│   x = 2  或  x = 3                              │
│                                                 │
│ 引擎          SymPy                             │
│ 驗證          精確代入（分數）                  │
│ 保證          VERIFIED-SUBSTITUTION             │
│ 結果          兩個根均滿足該方程式              │
└─────────────────────────────────────────────────┘
```

### 保證等級

並非每個數學結果都具有相同的邏輯強度。AXIOM 明確區分每一個等級：

| 等級 | 含義 |
| --- | --- |
| `exact-symbolic` | 已驗證的符號恆等式（例如正規化簡） |
| `verified-substitution` | 透過精確算術代入驗證的解 |
| `numerical-approximation` | 帶聲明誤差的數值近似 |
| `formal-proof` | 由證明核心（Lean 4）驗證的證明 |
| `heuristic` | 可能的結果，尚未完全驗證 |
| `unverified` | 原始計算，尚未驗證 |

每個結果都帶有證據中繼資料：`engine`、`engine_version`、`steps`、`limitations` 和 `reproducible_with`。

## 理念（繼承自 REA）

| REA | AXIOM |
| --- | --- |
| 逆向工程一切 | 分析數學 |
| 二進位分析 | 表達式與結構分析 |
| Ghidra / Hopper / IDA | SymPy / SageMath / Julia / Lean 4 |
| 程式碼追蹤 | 解追蹤 |
| 逆向工程證據 | 數學證據 |
| 反編譯 | 化簡與代數分解 |
| 函式檢查 | 函式分析 |
| 行為比較 | 等價性驗證 |
| 面向代理的 MCP | 面向數學代理的 MCP |
| CLI | 數學 CLI |

## 架構

```text
┌──────────────────────────────────────────────────────────┐
│  AI 代理                                                 │
│  Codex · Claude Code · Gemini CLI · 其他 MCP 用戶端      │
└────────────────────────┬─────────────────────────────────┘
                         │  MCP / CLI
┌────────────────────────▼─────────────────────────────────┐
│  AXIOM 核心                                              │
│  解析器 · 調度器 · 引擎註冊表 · 證據 ·                   │
│  驗證                                                    │
└──┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
 符號        數值        形式化      視覺化
 SymPy      SciPy       Lean 4     Plotly · Manim
 SageMath   Julia       Mathlib
```

無論由哪種軟體執行計算，同一契約始終成立：更換引擎既不會改變結果格式，也不會改變保證等級。

## 模組

| 模組 | 能力 |
| --- | --- |
| `arithmetic` | 精確算術、分數、任意精度 |
| `algebra` | 方程式、多項式、因式分解、化簡 |
| `calculus` | 極限、導數、積分、級數 |
| `linear-algebra` | 矩陣、特徵值、分解 |
| `geometry` | 歐幾里得幾何、解析幾何與微分幾何 |
| `number-theory` | 質數、同餘、丟番圖方程式 |
| `discrete` | 組合學、圖論、邏輯 |
| `statistics` | 機率、分布、推論 |
| `optimization` | 線性、非線性與凸優化 |
| `differential-equations` | 常微分方程、偏微分方程與動力系統 |
| `numerical` | 數值方法、近似與誤差 |
| `symbolic` | 通用符號操作 |
| `proof` | 證明、反例與形式化驗證 |
| `visualization` | 二維/三維繪圖、動畫與向量場 |
| `research` | 猜想探索、假設與實驗 |

## MCP 工具

小型、可組合的工具：

```
math_parse        math_simplify     math_solve
math_differentiate   math_integrate  math_limit
math_evaluate      math_plot         math_prove
math_verify        math_explain      math_compare
math_explore
```

提議的 CLI：

```bash
math solve "x^2 - 5*x + 6 = 0"
math integrate "sin(x)^2" --variable x
math plot "sin(x)/x" --range -10:10
math prove theorem.lean --engine lean
math verify solution.json
```

## 路線圖

- [ ] **v0.1 — 基礎**：CLI、MCP、表達式解析器、SymPy、方程式求解與證據。
- [ ] **v0.2 — 數值**：SciPy、矩陣、數值積分、優化與誤差評估。
- [ ] **v0.3 — 驗證**：獨立驗證器與可選的 Lean 4 整合。
- [ ] **v0.4 — 視覺化**：互動式繪圖、幾何與動力系統視覺化。
- [ ] **v1.0 — 研究**：自動化工具組合、可重現實驗與輔助猜想探索。

我們從三個引擎開始：**SymPy**（符號）、**SciPy**（數值）和 **Lean 4**（形式化證明）。

## 儲存庫結構

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

## 名稱

**AXIOM** —— *數學推理引擎*。它擁有獨立的身份，與形式數學與研究相一致。

## 授權條款

MIT

## 與 MathTools Offline 的關係

本儲存庫曾是 *MathTools Offline*（一個面向 LaTeX/SymPy/Lean 的離線桌面套件）。它被更名為 **AXIOM**，並重新定位為面向代理的計算數學基礎設施。引擎（SymPy、Lean 4）在概念上是共享的，但如今的重點是統一的 MCP 契約與結果的獨立驗證。
