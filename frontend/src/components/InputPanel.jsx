import React, { useState, useRef } from 'react';

const ALLOWED = ['pdf', 'docx', 'txt', 'md'];

export default function InputPanel({ inputMode, setInputMode, file, setFile, rawText, setRawText }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const handleFileDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && validateFile(f)) setFile(f);
  };

  const handleFileSelect = (e) => {
    const f = e.target.files[0];
    if (f && validateFile(f)) setFile(f);
  };

  const validateFile = (f) => {
    const ext = f.name.split('.').pop().toLowerCase();
    if (!ALLOWED.includes(ext)) {
      alert(`Unsupported file type: .${ext}\nAllowed: ${ALLOWED.join(', ')}`);
      return false;
    }
    return true;
  };

  return (
    <div className="card">
      <div className="card-title">
        <span className="icon">📝</span> Input Document
      </div>

      {/* Tab switcher */}
      <div className="tab-switcher">
        <button
          className={`tab-btn ${inputMode === 'file' ? 'active' : ''}`}
          onClick={() => setInputMode('file')}
          id="tab-file"
        >
          📂 Upload File
        </button>
        <button
          className={`tab-btn ${inputMode === 'text' ? 'active' : ''}`}
          onClick={() => setInputMode('text')}
          id="tab-text"
        >
          ✏️ Paste Text
        </button>
      </div>

      {/* File upload tab */}
      {inputMode === 'file' && (
        <>
          <div
            className={`drop-zone ${dragging ? 'dragging' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleFileDrop}
            onClick={() => inputRef.current?.click()}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,.txt,.md"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
              id="file-input"
            />
            <div className="drop-icon">📤</div>
            <h3>Drop your research paper here</h3>
            <p>Supports PDF, DOCX, TXT, MD &nbsp;·&nbsp; Max 20 MB</p>
          </div>

          {file && (
            <div className="file-selected">
              <span>✅</span>
              <span style={{ flex: 1 }}>{file.name}</span>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                {(file.size / 1024).toFixed(1)} KB
              </span>
              <button
                onClick={(e) => { e.stopPropagation(); setFile(null); }}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#f44336', fontSize: '1rem' }}
              >
                ✕
              </button>
            </div>
          )}
        </>
      )}

      {/* Text paste tab */}
      {inputMode === 'text' && (
        <>
          <textarea
            className="styled-textarea"
            placeholder={`Paste your research paper content here...\n\nExample:\nTitle: A Survey of Deep Learning Methods\nAuthors: John Smith, Jane Doe\nUniversity of Technology\n\nAbstract\nIn this paper we survey...\n\nI. Introduction\n...`}
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            id="raw-text-input"
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '6px' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {rawText.length.toLocaleString()} characters
            </span>
            {rawText && (
              <button
                onClick={() => setRawText('')}
                style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#ef9a9a', fontSize: '0.75rem' }}
              >
                Clear
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
