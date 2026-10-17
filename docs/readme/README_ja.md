# AXIOM

**数学推論エンジン**

*数学的な計算・探索・検証のための単一の MCP。*

[English](../../README.md) · [简体中文](README_zh.md) · [繁體中文](README_zh-TW.md) · **日本語** · [한국어](README_ko.md) · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md)

AXIOM は、AI エージェント、研究者、学生、開発者向けの計算数学インフラストラクチャです。統一された契約を通じて、あらゆる MCP クライアントを専門的な数学エンジン —— SymPy、SciPy、SageMath、Lean 4 —— に接続し、追跡可能で**独立して検証された**結果を提供します。

それは AI を搭載した電卓ではありません。もう一つの Mathematica、SageMath、Lean でもありません。エージェントがこれらすべてを単一のインターフェースを通じて利用できるようにするインフラストラクチャです。

> [REA](https://github.com/morluto/rea) の哲学に触発されて：*あらゆるものをリバースエンジニアリングする* → **数学を分析する**。

## AXIOM を選ぶ理由

エージェントは方程式を解いたと主張するかもしれません。AXIOM は結果が信頼される前に**独立した検証を要求します**。

```
math solve "x^2 - 5*x + 6 = 0"
```

```text
┌─────────────────────────────────────────────────┐
│ 二次方程式                                      │
│   x² - 5x + 6 = 0                               │
│                                                 │
│ 解                                              │
│   x = 2  または  x = 3                          │
│                                                 │
│ エンジン      SymPy                             │
│ 検証          正確な代入（分数）                │
│ 保証          VERIFIED-SUBSTITUTION             │
│ 結果          両方の根が方程式を満たす          │
└─────────────────────────────────────────────────┘
```

### 保証レベル

すべての数学的結果が同じ論理的強度を持つわけではありません。AXIOM は各レベルを明示的に区別します：

| レベル | 意味 |
| --- | --- |
| `exact-symbolic` | 検証済みの記号恒等式（例：正規化された簡約） |
| `verified-substitution` | 正確な算術による代入で検証された解 |
| `numerical-approximation` | 宣言された誤差を伴う数値近似 |
| `formal-proof` | 証明カーネル（Lean 4）によって検証された証明 |
| `heuristic` | もっともらしい結果だが、完全には検証されていない |
| `unverified` | 生の計算であり、まだ検証されていない |

すべての結果は証拠メタデータを伴います：`engine`、`engine_version`、`steps`、`limitations`、`reproducible_with`。

## 哲学（REA から受け継いだもの）

| REA | AXIOM |
| --- | --- |
| あらゆるものをリバースエンジニアリングする | 数学を分析する |
| バイナリ分析 | 式と構造の分析 |
| Ghidra / Hopper / IDA | SymPy / SageMath / Julia / Lean 4 |
| コードトレース | 解のトレース |
| リバースエンジニアリングの証拠 | 数学的証拠 |
| 逆コンパイル | 簡約と代数分解 |
| 関数の検査 | 関数分析 |
| 動作の比較 | 等価性の検証 |
| エージェントのための MCP | 数学エージェントのための MCP |
| CLI | 数学 CLI |

## アーキテクチャ

```text
┌──────────────────────────────────────────────────────────┐
│  AI エージェント                                         │
│  Codex · Claude Code · Gemini CLI · その他の MCP クライアント │
└────────────────────────┬─────────────────────────────────┘
                         │  MCP / CLI
┌────────────────────────▼─────────────────────────────────┐
│  AXIOM コア                                              │
│  パーサー · ディスパッチャー · エンジンレジストリ · 証拠 · │
│  検証                                                    │
└──┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
 記号        数値        形式        可視化
 SymPy      SciPy       Lean 4     Plotly · Manim
 SageMath   Julia       Mathlib
```

どのソフトウェアが計算を実行するかに関わらず、同じ契約が成り立ちます：エンジンを入れ替えても、結果の形式も保証レベルも変わりません。

## モジュール

| モジュール | 機能 |
| --- | --- |
| `arithmetic` | 正確な算術、分数、任意精度 |
| `algebra` | 方程式、多項式、因数分解、簡約 |
| `calculus` | 極限、導関数、積分、級数 |
| `linear-algebra` | 行列、固有値、分解 |
| `geometry` | ユークリッド幾何、解析幾何、微分幾何 |
| `number-theory` | 素数、合同式、ディオファントス方程式 |
| `discrete` | 組合せ論、グラフ、論理 |
| `statistics` | 確率、分布、推論 |
| `optimization` | 線形、非線形、凸最適化 |
| `differential-equations` | 常微分方程式、偏微分方程式、力学系 |
| `numerical` | 数値解法、近似、誤差 |
| `symbolic` | 一般的な記号操作 |
| `proof` | 証明、反例、形式検証 |
| `visualization` | 2D/3D プロット、アニメーション、ベクトル場 |
| `research` | 予想の探索、仮説、実験 |

## MCP ツール

小さく、組み合わせ可能なツール：

```
math_parse        math_simplify     math_solve
math_differentiate   math_integrate  math_limit
math_evaluate      math_plot         math_prove
math_verify        math_explain      math_compare
math_explore
```

提案されている CLI：

```bash
math solve "x^2 - 5*x + 6 = 0"
math integrate "sin(x)^2" --variable x
math plot "sin(x)/x" --range -10:10
math prove theorem.lean --engine lean
math verify solution.json
```

## ロードマップ

- [ ] **v0.1 — 基盤**：CLI、MCP、式パーサー、SymPy、方程式求解、証拠。
- [ ] **v0.2 — 数値**：SciPy、行列、数値積分、最適化、誤差評価。
- [ ] **v0.3 — 検証**：独立した検証器とオプションの Lean 4 統合。
- [ ] **v0.4 — 可視化**：インタラクティブなプロット、幾何、力学系の可視化。
- [ ] **v1.0 — 研究**：自動化されたツール構成、再現可能な実験、支援付きの予想探索。

私たちは 3 つのエンジンから始めます：**SymPy**（記号）、**SciPy**（数値）、**Lean 4**（形式証明）。

## リポジトリ構成

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

**AXIOM** —— *数学推論エンジン*。独自のアイデンティティを持ち、形式数学と研究に沿っています。

## ライセンス

MIT

## MathTools Offline との関係

このリポジトリはかつて *MathTools Offline*（LaTeX/SymPy/Lean 向けのオフラインデスクトップスイート）でした。**AXIOM** に改名され、エージェント向けの計算数学インフラストラクチャとして再位置づけられました。エンジン（SymPy、Lean 4）は概念的には共有されていますが、現在の焦点は統一された MCP 契約と結果の独立した検証にあります。
