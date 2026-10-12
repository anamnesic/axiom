import { useState, useEffect, useCallback } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";
import {
  fetchSympySession,
  execSympyCode,
  resetSympySession,
  fetchSympySymbols,
  evaluateExpression,
  differentiateExpression,
  solveEquation,
  simplifyExpression,
} from "../lib/api.js";

function escapeHtml(text) {
  return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

// O LaTeX vem do backend (sp.latex de uma expressão do usuário) e pode
// conter texto arbitrário em nomes de símbolos. Renderizar com KaTeX
// (que sanitiza a saída) — nunca injetar a string crua no DOM.
function renderLatex(latex) {
  try {
    return katex.renderToString(latex, {
      displayMode: false,
      throwOnError: true,
      trust: false,
    });
  } catch {
    return escapeHtml(latex);
  }
}

function SympyConsole() {
  const [session, setSession] = useState(null);
  const [cells, setCells] = useState([]);
  const [variables, setVariables] = useState([]);
  const [kernelStatus, setKernelStatus] = useState("starting");
  const [inputText, setInputText] = useState("");
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState("");

  const refreshSymbols = useCallback(() => {
    fetchSympySymbols()
      .then((res) => setVariables(res.symbols || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    resetSympySession().catch(() => {});
    fetchSympySession()
      .then((res) => {
        setSession(res);
        const initial = (res.cells || []).map((c) => ({
          ...c,
          output: null,
          loading: false,
          error: null,
        }));
        setCells(initial);
        setKernelStatus("ready");
      })
      .catch((err) => {
        setError("Failed to load session: " + err.message);
        setKernelStatus("error");
      });
  }, []);

  useEffect(() => {
    if (session && cells.length > 0) {
      evaluateAllCells();
    }
  }, [session]);

  async function evaluateAllCells() {
    setKernelStatus("executing");
    const updated = [];
    for (const cell of cells) {
      updated.push({ ...cell, loading: true, error: null });
      setCells([...updated]);
      try {
        const result = await execSympyCode(cell.code);
        updated[updated.length - 1] = {
          ...cell,
          loading: false,
          output: result.error
            ? { error: result.error }
            : { result: result.result, latex: result.latex, stdout: result.stdout },
          error: result.error || null,
        };
      } catch (err) {
        updated[updated.length - 1] = {
          ...cell,
          loading: false,
          output: null,
          error: err.message,
        };
      }
      setCells([...updated]);
    }
    refreshSymbols();
    setKernelStatus("idle");
  }

  async function handleExecute(code) {
    if (!code.trim()) return;
    setEvaluating(true);
    const newCell = {
      id: cells.length + 1,
      code: code.trim(),
      prompt: `In [${cells.length + 1}]`,
      type: "code",
      loading: true,
      output: null,
      error: null,
    };
    const updated = [...cells, newCell];
    setCells(updated);
    setInputText("");
    try {
      const result = await execSympyCode(code.trim());
      updated[updated.length - 1] = {
        ...newCell,
        loading: false,
        output: result.error
          ? { error: result.error }
          : { result: result.result, latex: result.latex, stdout: result.stdout },
        error: result.error || null,
      };
    } catch (err) {
      updated[updated.length - 1] = {
        ...newCell,
        loading: false,
        output: null,
        error: err.message,
      };
    }
    setCells([...updated]);
    refreshSymbols();
    setEvaluating(false);
  }

  async function handleOperation(op) {
    switch (op) {
      case "DERIVATIVE":
        setInputText("diff( , x)");
        break;
      case "INTEGRATE":
        setInputText("integrate( , x)");
        break;
      case "SUMMATION":
        setInputText("summation( , (x, 0, n))");
        break;
      case "LIMIT":
        setInputText("limit( , x, 0)");
        break;
      case "CURL":
        setInputText("curl( , (x y z))");
        break;
      case "CROSS":
        setInputText("cross( , )");
        break;
      case "SERIES":
        setInputText("series( , x, 0, 6)");
        break;
      case "LINSOLVE":
        setInputText("linsolve([x + y - 1, x - y - 2], (x, y))");
        break;
    }
  }

  function renderOutput(cell) {
    if (cell.loading) return <span style={{ color: "var(--outline)" }}>Computing...</span>;
    if (cell.error) return <span style={{ color: "var(--error)" }}>Error: {cell.error}</span>;
    if (!cell.output) return null;

    if (cell.output.error) {
      return <span style={{ color: "var(--error)" }}>{cell.output.error}</span>;
    }

    return (
      <>
        {cell.output.stdout && (
          <div style={{ fontFamily: "var(--font-code)", fontSize: "12px", color: "var(--on-surface-variant)", marginBottom: "4px", whiteSpace: "pre-wrap" }}>
            {cell.output.stdout}
          </div>
        )}
        {cell.output.latex && (
          <div
            className="output-math"
            style={{ fontSize: "16px", fontFamily: "var(--font-math)" }}
            dangerouslySetInnerHTML={{ __html: renderLatex(cell.output.latex) }}
          />
        )}
        {cell.output.result && !cell.output.latex && (
          <div className="output-math" style={{ fontSize: "14px", fontFamily: "var(--font-code)" }}>
            {cell.output.result}
          </div>
        )}
      </>
    );
  }

  return (
    <div className="console-workspace">
      <div className="console-main">
        <div className="console-header">
          <h2>{session?.title || "SymPy Session"}</h2>
          <p>
            {session?.python_version || "Python"} | {session?.sympy_version || "SymPy (Offline Core)"}.{" "}
            {session?.description || "Symbolic computation session."}
          </p>
        </div>

        <div className="console-cells">
          {cells.map((cell) => (
            <div key={cell.id}>
              <div className="input-cell" style={{ marginBottom: cell.output || cell.error ? "8px" : "0" }}>
                <div className="input-cell-inner">
                  <span className="input-prompt">{cell.prompt}:</span>
                  <div className="input-content">
                    <code
                      style={{
                        fontFamily: "var(--font-code)",
                        fontSize: "13px",
                        lineHeight: "20px",
                        color: "var(--on-surface)",
                        whiteSpace: "pre-wrap",
                      }}
                    >
                      {cell.code}
                    </code>
                  </div>
                </div>
              </div>
              {(cell.output || cell.error) && !cell.loading && (
                <div className="output-cell">
                  <div className="output-cell-inner">
                    <span className="output-prompt">
                      {cell.prompt.replace("In", "Out")}:
                    </span>
                    <div className="output-math">{renderOutput(cell)}</div>
                  </div>
                </div>
              )}
            </div>
          ))}

          <div className="input-cell">
            <div className="input-cell-inner">
              <span className="input-prompt">
                In [{cells.length + 1}]:
              </span>
              <div className="input-content" style={{ position: "relative" }}>
                <textarea
                  rows={3}
                  placeholder="Enter SymPy expression..."
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && e.shiftKey) {
                      e.preventDefault();
                      handleExecute(inputText);
                    }
                  }}
                  disabled={evaluating}
                />
                <div className="input-actions">
                  <button
                    className="input-run-btn"
                    onClick={() => handleExecute(inputText)}
                    disabled={evaluating || !inputText.trim()}
                  >
                    <span className="material-symbols-outlined" style={{ fontSize: "14px" }}>
                      play_arrow
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <aside className="console-inspector">
        <div className="inspector-tabs">
          <button className="inspector-tab active">VARIABLES</button>
          <button className="inspector-tab">FUNCTIONS</button>
        </div>
        <div className="inspector-body">
          <div>
            <div className="inspector-section-title">
              <span className="material-symbols-outlined">data_object</span>
              Live Scope
            </div>
            <div>
              {variables.length === 0 && (
                <div style={{ fontSize: "12px", color: "var(--on-surface-variant)", padding: "8px" }}>
                  No variables yet. Execute some code.
                </div>
              )}
              {variables.map((v) => (
                <div className="inspector-var" key={v.name}>
                  <div className="inspector-var-name">
                    {v.name}
                    <span className={`inspector-var-badge ${v.type === "Symbol" ? "symbol" : "expr"}`}>
                      {v.type}
                    </span>
                  </div>
                  <span className="inspector-var-type">{v.description}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginTop: "24px" }}>
            <div className="inspector-section-title">
              <span className="material-symbols-outlined">functions</span>
              Common Operations
            </div>
            <div className="inspector-grid">
              {["INTEGRATE", "DERIVATIVE", "SUMMATION", "LIMIT", "SERIES", "LINSOLVE"].map((op) => (
                <button key={op} className="inspector-grid-btn" onClick={() => handleOperation(op)}>
                  <span className="math-symbol">
                    {op === "INTEGRATE" ? "\u222B" : op === "DERIVATIVE" ? "d/dx" : op === "SUMMATION" ? "\u03A3" : op === "LIMIT" ? "lim" : op === "SERIES" ? "\u2211" : "\u00D7"}
                  </span>
                  <span className="btn-label">{op}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
        <div className="inspector-footer">
          <div className="inspector-status">
            <div className="inspector-status-left">
              <div
                className="status-dot"
                style={{
                  background: kernelStatus === "idle" ? "#00bcd4" : kernelStatus === "executing" ? "#ffb300" : kernelStatus === "error" ? "#ef5350" : "#9e9e9e",
                }}
              />
              <span style={{ fontSize: "12px", fontWeight: 700, color: "var(--on-surface-variant)", letterSpacing: "0.05em" }}>
                KERNEL {kernelStatus.toUpperCase()}
              </span>
            </div>
          </div>
        </div>
      </aside>

      <button className="fab" style={{ right: "340px" }}>
        <span className="material-symbols-outlined">add</span>
      </button>
    </div>
  );
}

export default SympyConsole;
