# Security Policy — Chronokairo AXIOM

> **Research Math for All Time by Chronokairo**

AXIOM executes mathematical and formal verification workflows that can be invoked autonomously by AI agents (e.g., Google Antigravity, Anthropic Claude Code, OpenAI Codex, Cursor). Because these agents have tool-use capabilities and execute local subprocesses, security, sandboxing, and input validation are treated as first-class architectural requirements.

---

## 1. Supported Versions

Security updates are applied to the active branch and published in the latest releases:

| Version | Supported | Status |
| :--- | :---: | :--- |
| `v0.2.8` | :white_check_mark: | Current stable release with evidence integrity & sandboxed Lean |
| `< v0.2.6` | :x: | Legacy versions; please upgrade to `v0.2.8` or newer |

---

## 2. Threat Model & Security Boundaries

AXIOM explicitly guards against several classes of agentic and mathematical threats:

1. **AST Injection & Code Execution (`Parser`)**:
   - The mathematical expression parser utilizes Python's built-in `ast` module with a strict node allowlist.
   - Any attempt to use Python builtins (`eval`, `exec`, `__import__`, `open`), access private object attributes (`__class__`, `__subclasses__`), or pass arbitrary code is blocked at parse time before evaluation.
2. **Path Traversal & MCP File Operations (`validate_mcp_path`)**:
   - File access via MCP tools (`math_plot`, `math_prove`, `math_verify`, `math_session`) is strictly constrained to authorized working project roots and dedicated temporary directories.
   - Absolute or relative traversal attempts (e.g., `../../etc/passwd` or system drive references) are rejected immediately with `Permission denied`.
3. **Subprocess Isolation for Proof Assistants (`LeanEngine`)**:
   - Lean 4 scripts run inside temporary sandboxes with scrubbed environments (`_build_sandboxed_env` strips all credentials, API keys, and sensitive environment variables).
   - Execution is bounded by memory limits (`-M 2048`), elaborator heartbeat limits (`-T 100000`), and strict subprocess timeouts.
4. **Evidence Tampering & Specification Spoofing**:
   - Serialized session entries and imported JSON files start in an unverified quarantine state (`revalidated_locally = False`, `guarantee = unverified`) until actively recomputed and validated locally.
   - Payloads claiming verified properties are checked for semantic equivalence against local execution outputs to prevent forged certificates.

---

## 3. Reporting a Vulnerability

If you discover a security vulnerability or soundness bypass in AXIOM:

1. **Do NOT open a public GitHub issue**.
2. Send a detailed report to the security team at **`security@chronokairo.com`** (or directly via the security contact on [chronokairo.com](https://chronokairo.com)).
3. Please include:
   - A description of the vulnerability and its potential impact.
   - A minimal reproducible example (code snippet, CLI command, or MCP JSON payload).
   - The environment, OS, and AXIOM version where the issue was reproduced.
4. We will acknowledge receipt within 48 hours and work with you on a coordinated disclosure timeline.
