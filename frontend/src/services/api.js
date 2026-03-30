/**
 * API service for AI Research Paper Formatter backend
 * All communication with Flask /process and /download endpoints
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

/**
 * Submit document for processing.
 * @param {Object} params
 * @param {File|null}   params.file
 * @param {string}      params.text
 * @param {string}      params.template  - ieee | springer | acm
 * @param {string}      params.format    - pdf | docx
 * @param {Object}      params.styling   - { fontFamily, titleSize, bodySize, lineSpacing }
 * @returns {Promise<Object>} API response JSON
 */
export async function processDocument({ file, text, template, format, styling }) {
  const form = new FormData();

  if (file) {
    form.append('file', file);
  } else {
    form.append('text', text);
  }

  form.append('template', template);
  form.append('format', format);

  if (styling.fontFamily) form.append('fontFamily', styling.fontFamily);
  if (styling.titleSize)  form.append('titleSize',  String(styling.titleSize));
  if (styling.bodySize)   form.append('bodySize',   String(styling.bodySize));
  if (styling.lineSpacing) form.append('lineSpacing', String(styling.lineSpacing));

  const response = await fetch(`${BASE_URL}/process`, {
    method: 'POST',
    body: form,
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || `Server error ${response.status}`);
  }

  return data;
}

/**
 * Build a full download URL for the given filename.
 */
export function getDownloadUrl(filename) {
  return `${BASE_URL}/download/${filename}`;
}

/**
 * Check backend health.
 */
export async function checkHealth() {
  try {
    const res = await fetch(`${BASE_URL}/health`);
    return res.ok;
  } catch {
    return false;
  }
}
