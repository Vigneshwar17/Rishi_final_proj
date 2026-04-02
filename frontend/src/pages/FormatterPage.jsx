import React, { useState, useEffect, useCallback } from "react";
import Navbar from "../components/Navbar.jsx";
import InputPanel from "../components/InputPanel.jsx";
import AuthorPanel from "../components/AuthorPanel.jsx";
import ConfigPanel from "../components/ConfigPanel.jsx";
import ResultPanel from "../components/ResultPanel.jsx";
import { processDocument, checkHealth } from "../services/api.js";

const DEFAULT_STYLING = {
  fontFamily: "Times New Roman",
  titleSize: 20,
  bodySize: 10,
  lineSpacing: 1.15,
};

export default function FormatterPage() {
  // Input state
  const [inputMode, setInputMode] = useState("file"); // 'file' | 'text'
  const [file, setFile] = useState(null);
  const [rawText, setRawText] = useState("");

  // Author state
  const [authors, setAuthors] = useState([
    {
      name: "",
      role: "Dr.",
      department: "",
      institution: "",
      email: "",
    },
  ]);

  // Config state
  const [template, setTemplate] = useState("ieee");
  const [outputFormat, setOutputFormat] = useState("pdf");
  const [styling, setStyling] = useState(DEFAULT_STYLING);

  // Processing state
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  // Backend health
  const [backendOnline, setBackendOnline] = useState(null);

  useEffect(() => {
    checkHealth().then((ok) => setBackendOnline(ok));
  }, []);

  const canSubmit =
    (inputMode === "file" ? !!file : rawText.trim().length > 20) &&
    !loading &&
    authors.some((a) => a.name && a.email);

  // Simulate progress while waiting for response
  const startFakeProgress = useCallback(() => {
    setProgress(0);
    const steps = [10, 25, 45, 65, 80, 90];
    let i = 0;
    const id = setInterval(() => {
      if (i < steps.length) {
        setProgress(steps[i++]);
      } else {
        clearInterval(id);
      }
    }, 600);
    return id;
  }, []);

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setError(null);
    setResult(null);
    setLoading(true);

    const progressId = startFakeProgress();

    try {
      const data = await processDocument({
        file: inputMode === "file" ? file : null,
        text: inputMode === "text" ? rawText : "",
        authors: authors.filter((a) => a.name && a.email),
        template,
        format: outputFormat,
        styling,
      });

      clearInterval(progressId);
      setProgress(100);

      if (data.success) {
        setTimeout(() => setResult(data), 300);
      } else {
        setError(data.error || "Unknown error from server.");
      }
    } catch (err) {
      clearInterval(progressId);
      setError(
        err.message || "Failed to connect to backend. Is the server running?",
      );
    } finally {
      setTimeout(() => {
        setLoading(false);
        setProgress(0);
      }, 400);
    }
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setFile(null);
    setRawText("");
    setProgress(0);
  };

  return (
    <div className="app-wrapper">
      <Navbar />

      <main className="main-content">
        {/* Header */}
        <div className="page-header">
          <div className="badge-row">
            <span className="badge badge-blue">IEEE · Springer · ACM</span>
            <span className="badge badge-green">NLP Powered</span>
            <span className="badge badge-purple">PDF · DOCX Output</span>
          </div>
          <h1>AI Research Paper Formatter</h1>
          <p>
            Upload any research document and get it intelligently converted into
            a properly structured academic paper — no hardcoded templates.
          </p>
        </div>

        {/* Backend status */}
        {backendOnline === false && (
          <div className="alert alert-error" style={{ marginBottom: "1.5rem" }}>
            🔴 Backend server is offline. Please start the Flask server on port
            5000 before submitting.
          </div>
        )}
        {backendOnline === true && (
          <div
            className="alert alert-success"
            style={{ marginBottom: "1.5rem" }}
          >
            🟢 Backend connected and ready.
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="alert alert-error" style={{ marginBottom: "1.5rem" }}>
            ❌ {error}
          </div>
        )}

        {/* Main workspace */}
        {!result ? (
          <div className="workspace">
            {/* Left Column: Input + Author (Stacked) */}
            <div className="workspace-left">
              {/* Top: Input */}
              <InputPanel
                inputMode={inputMode}
                setInputMode={setInputMode}
                file={file}
                setFile={setFile}
                rawText={rawText}
                setRawText={setRawText}
              />

              {/* Bottom: Author Details */}
              <AuthorPanel authors={authors} setAuthors={setAuthors} />
            </div>

            {/* Right Column: Config */}
            <ConfigPanel
              template={template}
              setTemplate={setTemplate}
              outputFormat={outputFormat}
              setOutputFormat={setOutputFormat}
              styling={styling}
              setStyling={setStyling}
              onSubmit={handleSubmit}
              loading={loading}
              progress={progress}
              canSubmit={canSubmit}
            />
          </div>
        ) : (
          <ResultPanel result={result} onReset={handleReset} />
        )}
      </main>

      <footer className="footer">
        AI Research Paper Formatter &nbsp;·&nbsp; Built with{" "}
        <span>NLP + ReportLab + python-docx</span>
      </footer>
    </div>
  );
}
