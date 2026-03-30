import React, { useState } from 'react';
import { getDownloadUrl } from '../services/api';

const SECTION_ICONS = {
  title: '📌', authors: '👥', abstract: '📋', keywords: '🏷️',
  sections: '📑', references: '📚', default: '✅',
};

function getSectionIcon(label) {
  const lower = label.toLowerCase();
  for (const [k, v] of Object.entries(SECTION_ICONS)) {
    if (lower.includes(k)) return v;
  }
  return SECTION_ICONS.default;
}

export default function ResultPanel({ result, onReset }) {
  const [editMode, setEditMode] = useState(false);
  const [editedTitle, setEditedTitle] = useState(result.document?.title || '');
  const [editedAbstract, setEditedAbstract] = useState(result.document?.abstract || '');

  const downloadUrl = getDownloadUrl(result.filename);
  const doc = result.document || {};

  return (
    <div className="result-panel">
      {/* Header */}
      <div className="result-header">
        <div className="result-title">
          ✅ Document Formatted Successfully
        </div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
          <button
            className="btn-download"
            onClick={() => window.open(downloadUrl, '_blank')}
            id="download-btn"
          >
            ⬇️ Download {result.filename?.split('.').pop()?.toUpperCase()}
          </button>
          <button
            onClick={onReset}
            style={{
              padding: '11px 18px', background: 'rgba(255,255,255,0.06)',
              border: '1px solid var(--border)', borderRadius: 'var(--radius-md)',
              color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.85rem',
              transition: 'var(--transition)',
            }}
            id="reset-btn"
          >
            🔄 Format Another
          </button>
        </div>
      </div>

      {/* Warnings */}
      {result.warnings?.length > 0 && (
        <div style={{ marginBottom: '1.25rem' }}>
          {result.warnings.map((w, i) => (
            <div key={i} className="alert alert-warning">⚠️ {w}</div>
          ))}
        </div>
      )}

      {/* Extraction error */}
      {result.extraction_error && (
        <div className="alert alert-error" style={{ marginBottom: '1.25rem' }}>
          🔴 Extraction note: {result.extraction_error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Detected Sections */}
        <div className="card">
          <div className="card-title"><span className="icon">🔍</span> Detected Sections</div>
          {result.detected_sections?.length > 0 ? (
            <div className="sections-grid">
              {result.detected_sections.map((s, i) => (
                <div key={i} className="section-chip">
                  <span className="chip-icon">{getSectionIcon(s)}</span>
                  <span style={{ textTransform: 'capitalize' }}>{s}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="alert alert-warning">No sections could be auto-detected.</div>
          )}

          {result.missing_sections?.length > 0 && (
            <>
              <div className="form-label" style={{ marginBottom: '8px', color: '#ef9a9a' }}>
                ⚠️ Missing Sections
              </div>
              <div className="sections-grid">
                {result.missing_sections.map((s, i) => (
                  <div key={i} className="missing-chip">
                    ❌ <span style={{ textTransform: 'capitalize' }}>{s}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>

        {/* Section Outline */}
        <div className="card">
          <div className="card-title"><span className="icon">📑</span> Section Outline</div>
          {doc.sections?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {doc.sections.map((s, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '8px 10px', background: 'rgba(0,0,0,0.2)',
                  borderRadius: 'var(--radius-sm)', fontSize: '0.8rem',
                  borderLeft: '2px solid var(--accent-blue)',
                }}>
                  <span style={{ color: 'var(--text-primary)', fontWeight: 500 }}>{s.heading}</span>
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.72rem' }}>
                    {s.paragraph_count} ¶
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="alert alert-warning">No body sections detected.</div>
          )}
          <div style={{ marginTop: '10px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            {doc.reference_count > 0 && `📚 ${doc.reference_count} references detected`}
          </div>
        </div>
      </div>

      {/* Document Preview + Edit */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-title" style={{ justifyContent: 'space-between' }}>
          <span><span className="icon">👁️</span> Extracted Content Preview</span>
          <button
            onClick={() => setEditMode(!editMode)}
            style={{
              padding: '5px 12px', background: editMode ? 'rgba(26,120,194,0.2)' : 'rgba(255,255,255,0.05)',
              border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)',
              color: 'var(--text-secondary)', cursor: 'pointer', fontSize: '0.75rem',
              transition: 'var(--transition)',
            }}
            id="edit-toggle-btn"
          >
            {editMode ? '💾 Done' : '✏️ Edit'}
          </button>
        </div>

        <div className="doc-preview">
          {/* Title */}
          <div className="form-label">Title</div>
          {editMode ? (
            <input
              className="editable-field"
              value={editedTitle}
              onChange={e => setEditedTitle(e.target.value)}
              id="edit-title"
            />
          ) : (
            <div className="preview-title">{doc.title || '(no title detected)'}</div>
          )}

          {/* Authors */}
          {doc.authors?.length > 0 && (
            <>
              <div className="form-label" style={{ marginTop: '10px' }}>Authors</div>
              <div className="preview-authors">
                {doc.authors.map((a, i) => (
                  <span key={i}>
                    {[a.name, a.institution, a.email].filter(Boolean).join(' · ')}
                    {i < doc.authors.length - 1 ? '  |  ' : ''}
                  </span>
                ))}
              </div>
            </>
          )}

          {/* Abstract */}
          {(doc.abstract || editMode) && (
            <>
              <div className="divider" />
              <div className="form-label">Abstract</div>
              {editMode ? (
                <textarea
                  className="editable-field"
                  value={editedAbstract}
                  onChange={e => setEditedAbstract(e.target.value)}
                  rows={4}
                  style={{ resize: 'vertical' }}
                  id="edit-abstract"
                />
              ) : (
                <div className="preview-abstract">{doc.abstract || '(no abstract detected)'}</div>
              )}
            </>
          )}

          {/* Keywords */}
          {doc.keywords?.length > 0 && (
            <>
              <div className="form-label" style={{ marginTop: '10px' }}>Keywords</div>
              <div className="preview-keywords">
                {doc.keywords.map((kw, i) => <span key={i} className="kw-chip">{kw}</span>)}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
