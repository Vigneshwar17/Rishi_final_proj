import React from 'react';

const TEMPLATES = [
  { id: 'ieee',     name: 'IEEE',     label: 'Institute of Electrical' },
  { id: 'springer', name: 'Springer', label: 'Nature Publisher' },
  { id: 'acm',      name: 'ACM',      label: 'Computing Machinery' },
];

const FORMATS = [
  { id: 'pdf',  label: '📄 PDF' },
  { id: 'docx', label: '📝 DOCX' },
];

const FONTS = [
  'Times New Roman',
  'Arial',
  'Helvetica',
  'Georgia',
  'Calibri',
];

export default function ConfigPanel({
  template, setTemplate,
  outputFormat, setOutputFormat,
  styling, setStyling,
  onSubmit,
  loading,
  progress,
  canSubmit,
}) {
  const update = (key, val) => setStyling(prev => ({ ...prev, [key]: val }));

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Template */}
      <div className="card">
        <div className="card-title"><span className="icon">🎓</span> Template</div>
        <div className="template-selector">
          {TEMPLATES.map(t => (
            <div
              key={t.id}
              className={`template-card ${template === t.id ? 'selected' : ''}`}
              onClick={() => setTemplate(t.id)}
              id={`template-${t.id}`}
              role="button"
              tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && setTemplate(t.id)}
            >
              <div className="tc-name">{t.name}</div>
              <div className="tc-label">{t.label}</div>
            </div>
          ))}
        </div>

        {/* Output format */}
        <div className="form-label" style={{ marginBottom: '8px' }}>Output Format</div>
        <div className="format-selector">
          {FORMATS.map(f => (
            <div
              key={f.id}
              className={`format-card ${outputFormat === f.id ? 'selected' : ''}`}
              onClick={() => setOutputFormat(f.id)}
              id={`format-${f.id}`}
              role="button"
              tabIndex={0}
              onKeyDown={e => e.key === 'Enter' && setOutputFormat(f.id)}
            >
              {f.label}
            </div>
          ))}
        </div>
      </div>

      {/* Styling */}
      <div className="card">
        <div className="card-title"><span className="icon">🎨</span> Styling</div>
        <div className="form-group">
          <label className="form-label" htmlFor="font-select">Font Family</label>
          <select
            id="font-select"
            className="form-select"
            value={styling.fontFamily}
            onChange={e => update('fontFamily', e.target.value)}
          >
            {FONTS.map(f => <option key={f} value={f}>{f}</option>)}
          </select>
        </div>

        <div className="styling-grid">
          <div className="slider-wrapper">
            <div className="slider-label-row">
              <span>Title Size</span>
              <span className="slider-val">{styling.titleSize}pt</span>
            </div>
            <input
              type="range" min="14" max="28" step="1"
              value={styling.titleSize}
              onChange={e => update('titleSize', Number(e.target.value))}
              id="title-size-slider"
            />
          </div>

          <div className="slider-wrapper">
            <div className="slider-label-row">
              <span>Body Size</span>
              <span className="slider-val">{styling.bodySize}pt</span>
            </div>
            <input
              type="range" min="8" max="14" step="1"
              value={styling.bodySize}
              onChange={e => update('bodySize', Number(e.target.value))}
              id="body-size-slider"
            />
          </div>

          <div className="slider-wrapper" style={{ gridColumn: '1/-1' }}>
            <div className="slider-label-row">
              <span>Line Spacing</span>
              <span className="slider-val">{styling.lineSpacing}×</span>
            </div>
            <input
              type="range" min="1" max="2" step="0.1"
              value={styling.lineSpacing}
              onChange={e => update('lineSpacing', Number(e.target.value))}
              id="line-spacing-slider"
            />
          </div>
        </div>
      </div>

      {/* Submit */}
      <button
        className="btn-submit"
        onClick={onSubmit}
        disabled={!canSubmit || loading}
        id="submit-btn"
      >
        {loading ? (
          <><span className="spinner"></span> Processing…</>
        ) : (
          '🚀 Format My Paper'
        )}
      </button>

      {loading && (
        <div className="progress-bar-wrap">
          <div className="progress-bar" style={{ width: `${progress}%` }} />
        </div>
      )}
    </div>
  );
}
