import React, { useState } from "react";
import "../styles/AuthorPanel.css";

export default function AuthorPanel({ authors, setAuthors }) {
  const [expandedIndex, setExpandedIndex] = useState(null);
  const [errors, setErrors] = useState({});

  const MAX_AUTHORS = 6;

  // Email validation
  const isValidEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  // Check for duplicate authors (by name or email)
  const hasDuplicate = (index, field, value) => {
    return authors.some(
      (author, i) =>
        i !== index && author[field].toLowerCase() === value.toLowerCase(),
    );
  };

  // Validate a single author
  const validateAuthor = (author, index) => {
    const newErrors = { ...errors };
    const authorKey = `author-${index}`;

    if (!newErrors[authorKey]) {
      newErrors[authorKey] = {};
    }

    // Check required fields
    if (!author.name.trim()) {
      newErrors[authorKey].name = "Name is required";
    } else if (hasDuplicate(index, "name", author.name)) {
      newErrors[authorKey].name = "This name already exists";
    } else {
      delete newErrors[authorKey].name;
    }

    if (!author.institution.trim()) {
      newErrors[authorKey].institution = "Institution is required";
    } else {
      delete newErrors[authorKey].institution;
    }

    if (!author.email.trim()) {
      newErrors[authorKey].email = "Email is required";
    } else if (!isValidEmail(author.email)) {
      newErrors[authorKey].email = "Invalid email format";
    } else if (hasDuplicate(index, "email", author.email)) {
      newErrors[authorKey].email = "This email already exists";
    } else {
      delete newErrors[authorKey].email;
    }

    if (Object.keys(newErrors[authorKey]).length === 0) {
      delete newErrors[authorKey];
    }

    setErrors(newErrors);
    return Object.keys(newErrors[authorKey] || {}).length === 0;
  };

  // Add new author
  const addAuthor = () => {
    if (authors.length >= MAX_AUTHORS) {
      alert(`Maximum ${MAX_AUTHORS} authors allowed`);
      return;
    }
    setAuthors([
      ...authors,
      {
        name: "",
        department: "",
        institution: "",
        email: "",
      },
    ]);
  };

  // Update author field
  const updateAuthor = (index, field, value) => {
    const updated = [...authors];
    updated[index][field] = value;
    setAuthors(updated);

    // Validate on change
    const authorKey = `author-${index}`;
    if (field === "name" || field === "email" || field === "institution") {
      if (!errors[authorKey] || errors[authorKey][field]) {
        validateAuthor(updated[index], index);
      }
    }
  };

  // Remove author
  const removeAuthor = (index) => {
    const updated = authors.filter((_, i) => i !== index);
    setAuthors(updated);

    // Clear errors for removed author
    const newErrors = { ...errors };
    delete newErrors[`author-${index}`];
    setErrors(newErrors);
  };

  return (
    <div className="card author-panel">
      <div className="card-title">
        <span className="icon">👥</span>
        Author Details ({authors.length}/{MAX_AUTHORS})
      </div>

      <div className="author-list">
        {authors.length === 0 ? (
          <div className="empty-state">
            <p>No authors added yet</p>
            <small>Click "Add Author" to get started</small>
          </div>
        ) : (
          authors.map((author, index) => {
            const authorKey = `author-${index}`;
            const authorErrors = errors[authorKey] || {};
            const hasErrors = Object.keys(authorErrors).length > 0;

            return (
              <div key={index} className="author-card">
                {/* Collapsed view */}
                <div
                  className="author-header"
                  onClick={() =>
                    setExpandedIndex(expandedIndex === index ? null : index)
                  }
                  style={{ cursor: "pointer" }}
                >
                  <div className="author-summary">
                    <span className="author-number">#{index + 1}</span>
                    <span className="author-name">
                      {author.name || "(No name entered)"}
                    </span>
                    {author.email && (
                      <span className="author-email">{author.email}</span>
                    )}
                    {hasErrors && <span className="error-badge">⚠️</span>}
                  </div>
                  <div className="header-actions">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        removeAuthor(index);
                      }}
                      className="btn btn-small btn-danger btn-icon"
                      title="Remove this author"
                    >
                      🗑️
                    </button>
                    <span className="expand-icon">
                      {expandedIndex === index ? "▼" : "▶"}
                    </span>
                  </div>
                </div>

                {/* Expanded view */}
                {expandedIndex === index && (
                  <div className="author-form">
                    {/* Full Name */}
                    <div className="form-row">
                      <div className="form-group flex-1">
                        <label htmlFor={`name-${index}`}>Full Name *</label>
                        <input
                          id={`name-${index}`}
                          type="text"
                          placeholder="e.g., John Smith"
                          value={author.name}
                          onChange={(e) =>
                            updateAuthor(index, "name", e.target.value)
                          }
                          className={`form-input ${
                            authorErrors.name ? "input-error" : ""
                          }`}
                        />
                        {authorErrors.name && (
                          <span className="error-message">
                            {authorErrors.name}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Institution */}
                    <div className="form-row">
                      <div className="form-group flex-1">
                        <label htmlFor={`institution-${index}`}>
                          Institution *
                        </label>
                        <input
                          id={`institution-${index}`}
                          type="text"
                          placeholder="e.g., MIT, Stanford University"
                          value={author.institution}
                          onChange={(e) =>
                            updateAuthor(index, "institution", e.target.value)
                          }
                          className={`form-input ${
                            authorErrors.institution ? "input-error" : ""
                          }`}
                        />
                        {authorErrors.institution && (
                          <span className="error-message">
                            {authorErrors.institution}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Department (Optional) */}
                    <div className="form-row">
                      <div className="form-group flex-1">
                        <label htmlFor={`department-${index}`}>
                          Department
                        </label>
                        <input
                          id={`department-${index}`}
                          type="text"
                          placeholder="e.g., Department of Computer Science"
                          value={author.department}
                          onChange={(e) =>
                            updateAuthor(index, "department", e.target.value)
                          }
                          className="form-input"
                        />
                      </div>
                    </div>

                    {/* Email */}
                    <div className="form-row">
                      <div className="form-group flex-1">
                        <label htmlFor={`email-${index}`}>
                          Email Address *
                        </label>
                        <input
                          id={`email-${index}`}
                          type="email"
                          placeholder="e.g., john.smith@mit.edu"
                          value={author.email}
                          onChange={(e) =>
                            updateAuthor(index, "email", e.target.value)
                          }
                          className={`form-input ${
                            authorErrors.email ? "input-error" : ""
                          }`}
                        />
                        {authorErrors.email && (
                          <span className="error-message">
                            {authorErrors.email}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="author-actions">
                      <button
                        onClick={() => validateAuthor(author, index)}
                        className="btn btn-small btn-success"
                        title="Validate this author"
                      >
                        ✓ Validate
                      </button>
                      <button
                        onClick={() => {
                          const newErrors = { ...errors };
                          delete newErrors[authorKey];
                          setErrors(newErrors);
                        }}
                        className="btn btn-small btn-secondary"
                        title="Clear errors"
                      >
                        🔄 Clear Errors
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Add Author Button */}
      <button
        onClick={addAuthor}
        className="btn btn-primary btn-block"
        disabled={authors.length >= MAX_AUTHORS}
        title={
          authors.length >= MAX_AUTHORS
            ? `Maximum ${MAX_AUTHORS} authors reached`
            : "Add a new author"
        }
      >
        ➕ Add Author
      </button>

      {/* Info box */}
      <div className="info-box">
        <span className="info-icon">ℹ️</span>
        <p>
          Enter author details here. All marked fields (*) are required. No
          duplicate names or emails allowed. Maximum {MAX_AUTHORS} authors.
        </p>
      </div>
    </div>
  );
}
