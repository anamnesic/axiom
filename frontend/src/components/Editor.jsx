import { useState, useEffect, useRef, useCallback } from "react";
import EditorMonaco, { loader } from "@monaco-editor/react";
import * as monaco from "monaco-editor";
import editorWorker from "monaco-editor/esm/vs/editor/editor.worker?worker";
import jsonWorker from "monaco-editor/esm/vs/language/json/json.worker?worker";
import cssWorker from "monaco-editor/esm/vs/language/css/css.worker?worker";
import htmlWorker from "monaco-editor/esm/vs/language/html/html.worker?worker";
import tsWorker from "monaco-editor/esm/vs/language/typescript/ts.worker?worker";
import katex from "katex";
import "katex/dist/katex.min.css";
import { fetchEditorTemplate, exportDocument } from "../lib/api.js";

// Monaco empacotado localmente (sem CDN): requisito do CSP estrito
// (script-src 'self') e do design offline do app.
self.MonacoEnvironment = {
  getWorker(_workerId, label) {
    switch (label) {
      case "json":
        return new jsonWorker();
      case "css":
      case "scss":
      case "less":
        return new cssWorker();
      case "html":
      case "handlebars":
      case "razor":
        return new htmlWorker();
      case "typescript":
      case "javascript":
        return new tsWorker();
      default:
        return new editorWorker();
    }
  },
};
loader.config({ monaco });

function extractMathBlocks(text) {
  const blocks = [];
  let i = 0;
  while (i < text.length) {
    const dStart = text.indexOf("$$", i);
    const sStart = text.indexOf("$", i);
    let start = -1, end = -1, isDisplay = false;

    if (dStart !== -1 && (sStart === -1 || dStart < sStart)) {
      start = dStart;
      isDisplay = true;
      end = text.indexOf("$$", start + 2);
    } else if (sStart !== -1) {
      start = sStart;
      isDisplay = false;
      end = text.indexOf("$", start + 1);
    }

    if (start === -1 || end === -1) break;

    const formula = text.slice(start + (isDisplay ? 2 : 1), end);
    const endIdx = end + (isDisplay ? 2 : 1);

    blocks.push({
      formula: formula.trim(),
      isDisplay,
      start,
      end: endIdx,
    });
    i = endIdx;
  }
  return blocks;
}

function Editor() {
  const [data, setData] = useState(null);
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(true);
  const [saveMsg, setSaveMsg] = useState("");
  const [exporting, setExporting] = useState(false);
  const [cursorPos, setCursorPos] = useState({ line: 1, col: 1 });
  const [renderedHtml, setRenderedHtml] = useState("");
  const [renderError, setRenderError] = useState("");
  const previewRef = useRef(null);
  const editorRef = useRef(null);

  useEffect(() => {
    fetchEditorTemplate()
      .then((res) => {
        setData(res);
        setCode(res.content);
      })
      .catch((err) => console.error("Failed to load editor template", err))
      .finally(() => setLoading(false));
  }, []);

  const renderPreview = useCallback((text) => {
    const blocks = extractMathBlocks(text);

    if (blocks.length === 0) {
      setRenderedHtml(`<div style="color:var(--on-surface-variant);font-style:italic;text-align:center;padding:48px;">
        No LaTeX math found. Use $...$ or $$...$$ blocks.
      </div>`);
      setRenderError("");
      return;
    }

    let html = "";
    let lastEnd = 0;
    let hasError = false;

    for (const block of blocks) {
      html += escapeHtml(text.slice(lastEnd, block.start));
      try {
        html += katex.renderToString(block.formula, {
          displayMode: block.isDisplay,
          throwOnError: true,
        });
      } catch (e) {
        hasError = true;
        html += `<span style="color:var(--error);border-bottom:1px wavy var(--error);">${escapeHtml(block.formula)}</span>`;
      }
      lastEnd = block.end;
    }
    html += escapeHtml(text.slice(lastEnd));

    setRenderedHtml(html || `<div style="color:var(--on-surface-variant);text-align:center;padding:48px;">Render preview</div>`);
    setRenderError(hasError ? "Some formulas contain errors" : "");
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => renderPreview(code), 300);
    return () => clearTimeout(timer);
  }, [code, renderPreview]);

  function escapeHtml(text) {
    return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function handleEditorDidMount(editor, monaco) {
    editorRef.current = editor;

    monaco.languages.register({ id: "latex" });
    monaco.languages.setMonarchTokensProvider("latex", {
      tokenizer: {
        root: [
          [/\\([a-zA-Z]+)/, "keyword"],
          [/\$/, "delimiter"],
          [/%.*$/, "comment"],
          [/[{}]/, "delimiter"],
          [/[0-9]+/, "number"],
        ],
      },
    });

    editor.onDidChangeCursorPosition((e) => {
      setCursorPos({ line: e.position.lineNumber, col: e.position.column });
    });
  }

  async function handleExport() {
    setExporting(true);
    try {
      const result = await exportDocument(code, "pdf");
      setSaveMsg(`PDF exported: ${result.file || "ok"}`);
    } catch (err) {
      setSaveMsg(`Export failed: ${err.message}`);
      if (err.message.includes("Typst CLI not found")) {
        setSaveMsg("Export: install Typst (winget install Typst.Typst)");
      }
    }
    setExporting(false);
    setTimeout(() => setSaveMsg(""), 3000);
  }

  async function handleSave() {
    try {
      const blob = new Blob([code], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = data?.filename || "document.tex";
      a.click();
      URL.revokeObjectURL(url);
      setSaveMsg("Saved to downloads");
    } catch (err) {
      setSaveMsg(`Save failed: ${err.message}`);
    }
    setTimeout(() => setSaveMsg(""), 2000);
  }

  function insertSymbol(symbol) {
    if (editorRef.current) {
      const sel = editorRef.current.getSelection();
      const range = new monaco.Range(sel.startLineNumber, sel.startColumn, sel.endLineNumber, sel.endColumn);
      editorRef.current.executeEdits("symbol-insert", [
        { range, text: symbol, forceMoveMarkers: true },
      ]);
      editorRef.current.focus();
    }
  }

  function handleEditorChange(value) {
    setCode(value || "");
  }

  if (loading) {
    return <div className="workspace-content" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>Loading template...</div>;
  }

  return (
    <>
      <div className="editor-toolbar">
        <div className="editor-toolbar-group">
          <button className="editor-toolbar-btn" title="Save" onClick={handleSave}>
            <span className="material-symbols-outlined">save</span>
          </button>
        </div>
        <div className="editor-toolbar-group">
          <button className="editor-toolbar-btn" title="Templates">
            <span className="material-symbols-outlined">category</span>
            Templates
          </button>
          <button className="editor-toolbar-btn" title="Symbols">
            <span className="material-symbols-outlined">calculate</span>
            Symbols
          </button>
        </div>
        <div className="editor-toolbar-spacer">
          <button className="editor-toolbar-primary" onClick={handleExport} disabled={exporting}>
            <span className="material-symbols-outlined">picture_as_pdf</span>
            {exporting ? "Exporting..." : "Export PDF"}
          </button>
        </div>
      </div>

      <div className="split-view">
        <div className="split-pane">
          <div className="pane-header">
            <span className="pane-header-label">{data?.filename || "document.tex"}</span>
            <span className="pane-header-info">Ln {cursorPos.line}, Col {cursorPos.col}</span>
          </div>
          <div className="code-editor" style={{ padding: 0 }}>
            <EditorMonaco
              height="100%"
              language="latex"
              theme="vs"
              value={code}
              onChange={handleEditorChange}
              onMount={handleEditorDidMount}
              options={{
                minimap: { enabled: false },
                lineNumbers: "on",
                glyphMargin: false,
                folding: false,
                lineDecorationsWidth: 8,
                lineNumbersMinChars: 3,
                padding: { top: 16, bottom: 16 },
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 13,
                lineHeight: 20,
                scrollBeyondLastLine: false,
                automaticLayout: true,
                wordWrap: "on",
                tabSize: 2,
                renderWhitespace: "selection",
              }}
            />
          </div>
        </div>

        <div className="split-pane" style={{ position: "relative" }}>
          <div className="pane-header">
            <span className="pane-header-label">Live Preview (KaTeX)</span>
          </div>
          <div className="math-preview">
            <div
              className="math-preview-inner katex-preview"
              ref={previewRef}
              dangerouslySetInnerHTML={{ __html: renderedHtml }}
            />
          </div>
          <div className="preview-status">
            <div className="preview-dot" style={{ background: renderError ? "var(--error)" : "var(--tertiary-fixed-dim)" }} />
            {renderError || saveMsg || "Live KaTeX Rendering"}
          </div>
        </div>
      </div>

      <footer className="status-bar">
        <div className="status-bar-left">
          <span className="status-bar-item">
            <span className="material-symbols-outlined">check_circle</span>
            UTF-8
          </span>
          <span className="status-bar-item">
            <span className="material-symbols-outlined">storage</span>
            {data ? `Local — ${code.split("\n").length} lines` : "Local Storage Only"}
          </span>
        </div>
        <div className="status-bar-right">
          <span>Ln {cursorPos.line} / {code.split("\n").length}</span>
          <span>v0.1.0</span>
        </div>
      </footer>

      <button className="fab">
        <span className="material-symbols-outlined">add</span>
        <div className="fab-menu">
          <div className="fab-menu-item" onClick={() => insertSymbol("\\pi")}>π</div>
          <div className="fab-menu-item" onClick={() => insertSymbol("\\int ")}>∫</div>
          <div className="fab-menu-item" onClick={() => insertSymbol("\\infty")}>∞</div>
          <div className="fab-menu-item" onClick={() => insertSymbol("\\nabla")}>∇</div>
        </div>
      </button>
    </>
  );
}

export default Editor;
