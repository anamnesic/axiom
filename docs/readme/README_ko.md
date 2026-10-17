# AXIOM

**수학 추론 엔진**

*수학적 계산, 탐구, 검증을 위한 단일 MCP.*

[English](../../README.md) · [简体中文](README_zh.md) · [繁體中文](README_zh-TW.md) · [日本語](README_ja.md) · **한국어** · [Türkçe](README_tr.md) · [Русский](README_ru.md) · [Tiếng Việt](README_vi.md) · [ไทย](README_th.md) · [Deutsch](README_de.md) · [Español](README_es.md) · [Français](README_fr.md) · [Português (Brasil)](README_pt-BR.md) · [العربية](README_ar.md) · [فارسی](README_fa.md) · [Italiano](README_it.md) · [Ελληνικά](README_el.md)

AXIOM은 AI 에이전트, 연구자, 학생, 개발자를 위한 계산 수학 인프라입니다. 통일된 계약을 통해 모든 MCP 클라이언트를 전문 수학 엔진 —— SymPy, SciPy, SageMath, Lean 4 —— 에 연결하고, 추적 가능하며 **독립적으로 검증된** 결과를 제공합니다.

그것은 AI 기반 계산기가 아닙니다. 또 다른 Mathematica, SageMath, Lean도 아닙니다. 에이전트가 이 모든 것을 단일 인터페이스로 사용할 수 있게 해 주는 인프라입니다.

> [REA](https://github.com/morluto/rea)의 철학에서 영감을 받았습니다: *무엇이든 리버스 엔지니어링한다* → **수학을 분석한다**.

## AXIOM을 선택하는 이유

에이전트는 방정식을 풀었다고 주장할 수 있습니다. AXIOM은 결과가 신뢰되기 전에 **독립적 검증을 요구합니다**.

```
math solve "x^2 - 5*x + 6 = 0"
```

```text
┌─────────────────────────────────────────────────┐
│ 이차방정식                                      │
│   x² - 5x + 6 = 0                               │
│                                                 │
│ 해                                              │
│   x = 2  또는  x = 3                            │
│                                                 │
│ 엔진          SymPy                             │
│ 검증          정확한 대입(분수)                 │
│ 보증          VERIFIED-SUBSTITUTION             │
│ 결과          두 근 모두 방정식을 만족          │
└─────────────────────────────────────────────────┘
```

### 보증 수준

모든 수학적 결과가 동일한 논리적 강도를 지니지는 않습니다. AXIOM은 각 수준을 명확히 구분합니다:

| 수준 | 의미 |
| --- | --- |
| `exact-symbolic` | 검증된 기호 항등식(예: 정규화된 단순화) |
| `verified-substitution` | 정확한 산술로 대입하여 검증된 해 |
| `numerical-approximation` | 선언된 오차를 동반한 수치 근사 |
| `formal-proof` | 증명 커널(Lean 4)로 검증된 증명 |
| `heuristic` | 그럴듯하지만 완전히 검증되지 않은 결과 |
| `unverified` | 아직 검증되지 않은 원시 계산 |

모든 결과는 증거 메타데이터를 포함합니다: `engine`, `engine_version`, `steps`, `limitations`, `reproducible_with`.

## 철학 (REA에서 계승)

| REA | AXIOM |
| --- | --- |
| 무엇이든 리버스 엔지니어링한다 | 수학을 분석한다 |
| 바이너리 분석 | 표현식 및 구조 분석 |
| Ghidra / Hopper / IDA | SymPy / SageMath / Julia / Lean 4 |
| 코드 추적 | 해 추적 |
| 리버스 엔지니어링 증거 | 수학적 증거 |
| 디컴파일 | 단순화 및 대수적 분해 |
| 함수 검사 | 함수 분석 |
| 동작 비교 | 동등성 검증 |
| 에이전트를 위한 MCP | 수학 에이전트를 위한 MCP |
| CLI | 수학 CLI |

## 아키텍처

```text
┌──────────────────────────────────────────────────────────┐
│  AI 에이전트                                             │
│  Codex · Claude Code · Gemini CLI · 기타 MCP 클라이언트  │
└────────────────────────┬─────────────────────────────────┘
                         │  MCP / CLI
┌────────────────────────▼─────────────────────────────────┐
│  AXIOM 코어                                              │
│  파서 · 디스패처 · 엔진 레지스트리 · 증거 ·              │
│  검증                                                    │
└──┬──────────┬──────────┬──────────┬───────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
 기호        수치        형식       시각화
 SymPy      SciPy       Lean 4     Plotly · Manim
 SageMath   Julia       Mathlib
```

어떤 소프트웨어가 계산을 수행하든 동일한 계약이 유지됩니다: 엔진을 교체해도 결과 형식이나 보증 수준은 바뀌지 않습니다.

## 모듈

| 모듈 | 기능 |
| --- | --- |
| `arithmetic` | 정확한 산술, 분수, 임의 정밀도 |
| `algebra` | 방정식, 다항식, 인수분해, 단순화 |
| `calculus` | 극한, 도함수, 적분, 급수 |
| `linear-algebra` | 행렬, 고유값, 분해 |
| `geometry` | 유클리드 기하, 해석 기하, 미분 기하 |
| `number-theory` | 소수, 합동, 디오판토스 방정식 |
| `discrete` | 조합론, 그래프, 논리 |
| `statistics` | 확률, 분포, 추론 |
| `optimization` | 선형, 비선형, 볼록 최적화 |
| `differential-equations` | 상미분방정식, 편미분방정식, 동역학계 |
| `numerical` | 수치 해법, 근사, 오차 |
| `symbolic` | 일반 기호 조작 |
| `proof` | 증명, 반례, 형식 검증 |
| `visualization` | 2D/3D 플롯, 애니메이션, 벡터장 |
| `research` | 추측 탐구, 가설, 실험 |

## MCP 도구

작고 조합 가능한 도구:

```
math_parse        math_simplify     math_solve
math_differentiate   math_integrate  math_limit
math_evaluate      math_plot         math_prove
math_verify        math_explain      math_compare
math_explore
```

제안된 CLI:

```bash
math solve "x^2 - 5*x + 6 = 0"
math integrate "sin(x)^2" --variable x
math plot "sin(x)/x" --range -10:10
math prove theorem.lean --engine lean
math verify solution.json
```

## 로드맵

- [ ] **v0.1 — 기반**: CLI, MCP, 표현식 파서, SymPy, 방정식 풀이, 증거.
- [ ] **v0.2 — 수치**: SciPy, 행렬, 수치 적분, 최적화, 오차 평가.
- [ ] **v0.3 — 검증**: 독립 검증기와 선택적 Lean 4 통합.
- [ ] **v0.4 — 시각화**: 대화형 플롯, 기하, 동역학계 시각화.
- [ ] **v1.0 — 연구**: 자동화된 도구 구성, 재현 가능한 실험, 지원되는 추측 탐구.

우리는 세 가지 엔진으로 시작합니다: **SymPy**(기호), **SciPy**(수치), **Lean 4**(형식 증명).

## 저장소 구조

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

## 이름

**AXIOM** —— *수학 추론 엔진*. 형식 수학과 연구에 부합하는 고유한 정체성.

## 라이선스

MIT

## MathTools Offline과의 관계

이 저장소는 한때 *MathTools Offline*(LaTeX/SymPy/Lean을 위한 오프라인 데스크톱 제품군)이었습니다. **AXIOM**으로 이름이 바뀌고 에이전트를 위한 계산 수학 인프라로 재정립되었습니다. 엔진(SymPy, Lean 4)은 개념적으로 공유되지만, 이제 초점은 통일된 MCP 계약과 결과의 독립적 검증입니다.
