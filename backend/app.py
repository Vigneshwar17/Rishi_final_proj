"""
Flask Backend - AI Research Paper Formatter
POST /process  → parse + generate document
GET  /download/<filename> → serve generated file
GET  /health   → health check
"""

import os
import uuid
import logging
import traceback
from dataclasses import asdict

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Internal modules
from utils.file_extractor import extract_from_file, extract_from_text
from parser.nlp_parser import parse_document
from generators.pdf_generator import generate_pdf
from generators.docx_generator import generate_docx

# ─────────────────────────────────────────────
#  Setup
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
IMAGES_DIR = os.path.join(BASE_DIR, "images")

os.makedirs(OUTPUTS_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {"pdf", "docx", "txt", "md"}
MAX_CONTENT_LENGTH = 20 * 1024 * 1024  # 20 MB

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
CORS(app, origins="*")


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def serialize_doc(doc_data) -> dict:
    """Convert DocumentData to a JSON-serialisable dict."""
    def _ser(obj):
        if hasattr(obj, "__dataclass_fields__"):
            return {k: _ser(v) for k, v in asdict(obj).items()}
        elif isinstance(obj, list):
            return [_ser(i) for i in obj]
        else:
            return obj

    return _ser(doc_data)


# ─────────────────────────────────────────────
#  Routes
# ─────────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "AI Research Paper Formatter is running."})


@app.route("/process", methods=["POST"])
def process():
    """
    Expected multipart/form-data fields:
      file       – uploaded file (optional)
      text       – raw text input (optional, used if no file)
      template   – ieee | springer | acm  (default: ieee)
      format     – pdf | docx             (default: pdf)
      fontFamily – font family name       (optional)
      titleSize  – integer pt             (optional)
      bodySize   – integer pt             (optional)
      lineSpacing – float                 (optional)
    """
    try:
        # ── 1. Gather inputs ────────────────────────────────
        template = request.form.get("template", "ieee").lower()
        output_format = request.form.get("format", "pdf").lower()

        styling = {
            "fontFamily": request.form.get("fontFamily", ""),
            "titleSize": request.form.get("titleSize", ""),
            "bodySize": request.form.get("bodySize", ""),
            "lineSpacing": request.form.get("lineSpacing", ""),
        }
        # Remove empty styling values so generators use defaults
        styling = {k: v for k, v in styling.items() if v}

        # ── 2. Extract raw text ──────────────────────────────
        raw_text = ""
        extraction_error = None

        if "file" in request.files and request.files["file"].filename:
            file = request.files["file"]
            if not allowed_file(file.filename):
                return jsonify({"success": False, "error": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400
            result = extract_from_file(file)
            raw_text = result["text"]
            extraction_error = result.get("error")
        elif request.form.get("text", "").strip():
            raw_text = request.form.get("text", "").strip()
        else:
            return jsonify({"success": False, "error": "No input provided. Upload a file or paste text."}), 400

        if not raw_text.strip():
            return jsonify({"success": False, "error": "No readable text found in the input."}), 400

        # ── 3. Parse ──────────────────────────────────────────
        logger.info(f"Parsing document | template={template} | format={output_format}")
        doc_data = parse_document(raw_text)

        # ── 4. Generate output file ──────────────────────────
        uid = uuid.uuid4().hex[:10]
        if output_format == "docx":
            filename = f"paper_{uid}.docx"
            out_path = os.path.join(OUTPUTS_DIR, filename)
            generate_docx(doc_data, out_path, template=template, styling=styling)
        else:
            filename = f"paper_{uid}.pdf"
            out_path = os.path.join(OUTPUTS_DIR, filename)
            generate_pdf(doc_data, out_path, template=template, styling=styling)

        # ── 5. Build response ────────────────────────────────
        response = {
            "success": True,
            "detected_sections": doc_data.detected_sections,
            "missing_sections": doc_data.missing_sections,
            "warnings": doc_data.warnings,
            "document": {
                "title": doc_data.title,
                "authors": [
                    {
                        "name": a.name,
                        "email": a.email,
                        "institution": a.institution,
                        "department": a.department,
                        "role": a.role,
                    }
                    for a in doc_data.authors
                ],
                "abstract": doc_data.abstract[:400] + ("..." if len(doc_data.abstract) > 400 else ""),
                "keywords": doc_data.keywords,
                "section_count": len(doc_data.sections),
                "reference_count": len(doc_data.references),
                "sections": [
                    {"heading": s.heading, "paragraph_count": len(s.paragraphs)}
                    for s in doc_data.sections
                ],
            },
            "download_url": f"/download/{filename}",
            "filename": filename,
            "extraction_error": extraction_error,
        }

        logger.info(f"Document generated: {filename}")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Processing error: {traceback.format_exc()}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@app.route("/download/<path:filename>", methods=["GET"])
def download(filename):
    """Serve a generated file for download."""
    safe_name = secure_filename(filename)
    return send_from_directory(OUTPUTS_DIR, safe_name, as_attachment=True)


# ─────────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
