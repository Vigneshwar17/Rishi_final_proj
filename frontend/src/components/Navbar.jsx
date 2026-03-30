import React from 'react';

export default function Navbar() {
  return (
    <nav className="navbar">
      <a className="navbar-logo" href="/">
        <div className="navbar-logo-icon">📄</div>
        <span className="navbar-logo-text">
          AI<span>Paper</span>Formatter
        </span>
      </a>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span className="navbar-badge">NLP Powered</span>
      </div>
    </nav>
  );
}
